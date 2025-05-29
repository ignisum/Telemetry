using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Server.Data;
using Server.Hubs;
using Server.Models;

namespace Server.Services
{
    public class TelemetryService : BackgroundService
    {
        private readonly IServiceProvider _services;
        private readonly IHubContext<TelemetryHub> _hubContext;
        private readonly ILogger<TelemetryService> _logger;

        private int _packetCounter = 0;
        private bool _isRunning = false;
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

                _currentSessionId = (int?)session.Id;
                return (int)session.Id;
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
                if (_isRunning && _currentSessionId.HasValue)
                {
                    await using var scope = _services.CreateAsyncScope();
                    var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

                    try
                    {
                        if (!await dbContext.Database.CanConnectAsync(stoppingToken))
                        {
                            _logger.LogError("Нет подключения к БД! Повторная попытка через 5 секунд...");
                            await Task.Delay(5000, stoppingToken);
                            continue;
                        }

                        var packet = new TelemetryPacket
                        {
                            PacketCounter = _packetCounter++,
                            Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
                            Payload = Math.Sin(new Random().NextDouble() * 2 * Math.PI),
                            SessionId = _currentSessionId.Value
                        };

                        packet.Crc16 = ComputeCrc16(packet);

                        await dbContext.Packets.AddAsync(packet, stoppingToken);
                        await dbContext.SaveChangesAsync(stoppingToken);
                        await _hubContext.Clients.All.SendAsync("NewPacket", packet, stoppingToken);

                        _logger.LogDebug($"Отправлен пакет {packet.Id} в сессии {CurrentSessionId}");
                    }
                    catch (Npgsql.PostgresException ex)
                    {
                        _logger.LogError(ex, "Ошибка PostgreSQL");
                        await Task.Delay(10000, stoppingToken);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Ошибка в сервисе телеметрии");
                        await Task.Delay(5000, stoppingToken);
                    }
                    finally
                    {
                        await EnsureConnectionClosedAsync(dbContext);
                    }
                }

                await Task.Delay(2000, stoppingToken);
            }
        }

        public void StartGeneration(long? sessionId = null)
        {
            if (sessionId.HasValue)
            {
                _currentSessionId = sessionId.Value;
            }

            if (!CurrentSessionId.HasValue)
            {
                _logger.LogWarning("Попытка запуска генерации без активной сессии");
                return;
            }

            _isRunning = true;
            _logger.LogInformation($"Генерация запущена для сессии {CurrentSessionId}");
        }

        public async Task StopGeneration()
        {
            if (_currentSessionId.HasValue)
            {
                await using var scope = _services.CreateAsyncScope();
                var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

                try
                {
                    var session = await dbContext.Sessions.FindAsync(_currentSessionId);
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

            _isRunning = false;
            _logger.LogInformation("Генерация данных остановлена");
        }

        public override async Task StopAsync(CancellationToken cancellationToken)
        {
            _logger.LogInformation("Остановка сервиса телеметрии...");

            try
            {
                if (_isRunning)
                {
                    await StopGeneration();
                }
            }
            finally
            {
                await base.StopAsync(cancellationToken);
            }
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
}