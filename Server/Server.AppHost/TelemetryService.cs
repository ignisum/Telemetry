using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Server.Data;
using Server.Hubs;
using Server.Models;
using System.Collections.Concurrent;

namespace Server.Services
{
    public class TelemetryService : BackgroundService
    {
        private readonly IServiceProvider _services;
        private readonly IHubContext<TelemetryHub> _hubContext;
        private readonly ILogger<TelemetryService> _logger;
        private readonly ConcurrentDictionary<long, SessionGenerator> _activeSessions = new();
        private readonly ConcurrentDictionary<long, int> _sessionPacketCounters = new();

        private long? _currentSessionId;

        public long? CurrentSessionId
        {
            get => _currentSessionId;
            set => _currentSessionId = value;
        }

        public TelemetryService(
            IServiceProvider services,
            IHubContext<TelemetryHub> hubContext,
            ILogger<TelemetryService> logger)
        {
            _services = services;
            _hubContext = hubContext;
            _logger = logger;
        }

        public async Task<long> StartNewSession(string name)
        {
            await using var scope = _services.CreateAsyncScope();
            var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

            try
            {
                var session = new Session
                {
                    Name = name,
                    StartTime = DateTime.UtcNow
                };

                dbContext.Sessions.Add(session);
                await dbContext.SaveChangesAsync();

                return session.Id;
            }
            finally
            {
                await EnsureConnectionClosedAsync(dbContext);
            }
        }

        public async Task EndCurrentSession()
        {
            if (!CurrentSessionId.HasValue) return;

            await using var scope = _services.CreateAsyncScope();
            var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

            try
            {
                var session = await dbContext.Sessions.FindAsync(CurrentSessionId);
                if (session != null)
                {
                    session.EndTime = DateTime.UtcNow;
                    await dbContext.SaveChangesAsync();
                }
            }
            finally
            {
                await EnsureConnectionClosedAsync(dbContext);
                _currentSessionId = null;
            }
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("Сервис телеметрии запущен");

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    foreach (var session in _activeSessions)
                    {
                        if (session.Value.IsRunning)
                        {
                            await GeneratePacketForSession(session.Key);
                        }
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Ошибка в сервисе телеметрии");
                }

                await Task.Delay(2000, stoppingToken);
            }
        }

        private async Task GeneratePacketForSession(long sessionId)
        {
            await using var scope = _services.CreateAsyncScope();
            var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

            try
            {
                if (!await dbContext.Database.CanConnectAsync())
                {
                    _logger.LogError("Нет подключения к БД");
                    return;
                }

                int packetCounter = _sessionPacketCounters.AddOrUpdate(
                    sessionId,
                    0,
                    (id, count) => count + 1);

                var packet = new TelemetryPacket
                {
                    PacketCounter = packetCounter,
                    Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
                    Payload = Math.Sin(new Random().NextDouble() * 2 * Math.PI),
                    SessionId = sessionId
                };

                packet.Crc16 = ComputeCrc16(packet);

                await dbContext.Packets.AddAsync(packet);
                await dbContext.SaveChangesAsync();

                await _hubContext.Clients.Group($"session-{sessionId}")
                    .SendAsync("NewPacket", packet);

                _logger.LogDebug($"Паект {packet.Id} отправлен для сессии {sessionId}");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Ошибка генерации пакета для сессии {sessionId}");
            }
            finally
            {
                await EnsureConnectionClosedAsync(dbContext);
            }
        }

        public void StartGeneration(long sessionId)
        {
            _activeSessions.AddOrUpdate(
                sessionId,
                id => new SessionGenerator { IsRunning = true },
                (id, state) => {
                    state.IsRunning = true;
                    return state;
                });

            _sessionPacketCounters.TryAdd(sessionId, 0);

            _logger.LogInformation($"Генерация начата для сессии {sessionId}. Активных сессий: {_activeSessions.Count}");
        }
        public async Task StopGeneration(long sessionId)
        {
            if (_activeSessions.TryRemove(sessionId, out var generator))
            {
                generator.IsRunning = false;

                await using var scope = _services.CreateAsyncScope();
                var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

                try
                {
                    var session = await dbContext.Sessions.FindAsync(sessionId);
                    if (session != null)
                    {
                        session.EndTime = DateTime.UtcNow;
                        await dbContext.SaveChangesAsync();
                        _logger.LogInformation($"Сессиия {sessionId} сохранена в БД");
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, $"Ошибка при завершении сеанса {sessionId}");
                }
                finally
                {
                    await EnsureConnectionClosedAsync(dbContext);
                }

                await _hubContext.Clients.Group($"session-{sessionId}")
                    .SendAsync("GenerationStopped", sessionId);

                _logger.LogInformation($"Генерация данных остановлена для сессии {sessionId}");
            }
            else
            {
                _logger.LogWarning($"Попытка завершить несуществующую сессию {sessionId}");
            }
        }

        public override async Task StopAsync(CancellationToken cancellationToken)
        {
            _logger.LogInformation("Остановка сервиса телеметрии...");

            foreach (var sessionId in _activeSessions.Keys)
            {
                await StopGeneration(sessionId);
            }

            await base.StopAsync(cancellationToken);
        }

        private static int ComputeCrc16(TelemetryPacket packet)
        {
            int crc = 0xFFFF;
            var bytes = BitConverter.GetBytes(packet.Payload)
                .Concat(BitConverter.GetBytes(packet.PacketCounter))
                .Concat(BitConverter.GetBytes(packet.Timestamp))
                .ToArray();

            foreach (byte b in bytes)
            {
                crc ^= (ushort)(b << 8);
                for (int i = 0; i < 8; i++)
                {
                    crc = (crc & 0x8000) != 0 ? (ushort)((crc << 1) ^ 0x1021) : (ushort)(crc << 1);
                }
            }
            return crc;
        }

        private async Task EnsureConnectionClosedAsync(ApplicationContext dbContext)
        {
            try
            {
                if (dbContext.Database.GetDbConnection().State == System.Data.ConnectionState.Open)
                {
                    await dbContext.Database.CloseConnectionAsync();
                    _logger.LogDebug("Соединение с БД закрыто");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Ошибка при закрытии соединения с БД");
            }
        }
    }

    public class SessionGenerator
    {
        public bool IsRunning { get; set; } = true;
    }
}