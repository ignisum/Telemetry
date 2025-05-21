using Microsoft.AspNetCore.SignalR;
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
        private uint _packetCounter = 0;
        private readonly ILogger<TelemetryService> _logger;
        private bool _isRunning = false;
        private int? _currentSessionId;
        public int? CurrentSessionId
        {
            get => _currentSessionId;
            set => _currentSessionId = value;
        }

        public TelemetryService(IServiceProvider services, IHubContext<TelemetryHub> hubContext, ILogger<TelemetryService> logger)
        {
            _services = services;
            _hubContext = hubContext;
            _logger = logger;
        }

        public async Task<int> StartNewSession(string name)
        {
            using var scope = _services.CreateScope();
            var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

            var session = new Session
            {
                Name = name,
                StartTime = DateTime.UtcNow
            };

            dbContext.Sessions.Add(session);
            await dbContext.SaveChangesAsync();

            _currentSessionId = session.Id;
            return session.Id;
        }

        public async Task EndCurrentSession()
        {
            if (!CurrentSessionId.HasValue) return;

            using var scope = _services.CreateScope();
            var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
            var session = await dbContext.Sessions.FindAsync(CurrentSessionId);
            if (session != null)
            {
                session.EndTime = DateTime.UtcNow;
                await dbContext.SaveChangesAsync();
            }

            _currentSessionId = null;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("Сервис телеметрии запущен");

            while (!stoppingToken.IsCancellationRequested)
            {
                if (_isRunning && _currentSessionId.HasValue)
                {
                    try
                    {
                        using var scope = _services.CreateScope();
                        var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

                        var packet = new TelemetryPacket
                        {
                            PacketCounter = _packetCounter++,
                            Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
                            Payload = Math.Sin(new Random().NextDouble() * 2 * Math.PI),
                            SessionId = _currentSessionId.Value
                        };

                        packet.Crc16 = ComputeCrc16(packet);

                        dbContext.Packets.Add(packet);
                        await dbContext.SaveChangesAsync(stoppingToken);

                        await _hubContext.Clients.All.SendAsync("NewPacket", packet, stoppingToken);

                        _logger.LogInformation($"Отправлен пакет {packet.Id} в сессии {CurrentSessionId}");
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Ошибка генерации пакета");
                    }
                }
                await Task.Delay(2000, stoppingToken);
            }
        }

        public void StartGeneration(int? sessionId = null)
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
                using var scope = _services.CreateScope();
                var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
                var session = await dbContext.Sessions.FindAsync(_currentSessionId);
                if (session != null)
                {
                    session.EndTime = DateTime.UtcNow;
                    await dbContext.SaveChangesAsync();
                }
                _currentSessionId = null;
            }

            _isRunning = false;
        }

        private static ushort ComputeCrc16(TelemetryPacket packet)
        {
            ushort crc = 0xFFFF;
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
    }
}