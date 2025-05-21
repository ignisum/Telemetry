using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Server.Data;
using Server.Services;

namespace Server.Controllers
{ 
    [ApiController]
    [Route("api/[controller]")]
    public class TelemetryController : ControllerBase
    {
        private readonly TelemetryService _telemetryService;
        private readonly IServiceProvider _services;
        private readonly ILogger _logger;

        public TelemetryController(TelemetryService telemetryService, IServiceProvider services, ILogger<TelemetryService> logger)
        {
            _telemetryService = telemetryService;
            _services = services;
            _logger = logger;
        }

        [HttpPost("start")]
        public IActionResult StartGeneration([FromBody] StartRequest request)
        {
            if (request?.SessionId != null)
            {
                _telemetryService.CurrentSessionId = request.SessionId.Value;
            }

            _telemetryService.StartGeneration(request?.SessionId);
            return Ok(new
            {
                Message = "Генерация данных запущена",
                SessionId = _telemetryService.CurrentSessionId
            });
        }

        [HttpPost("stop")]
        public IActionResult StopGeneration()
        {
            _telemetryService.StopGeneration();
            return Ok("Генерация данных остановлена");
        }

        [HttpGet("status")]
        public IActionResult GetStatus() => Ok("Сервер работает");

        [HttpGet("sessions")]
        public async Task<IActionResult> GetAllSessions()
        {
            using var scope = _services.CreateScope();
            var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationContext>();

            var sessions = await dbContext.Sessions
                .OrderByDescending(s => s.StartTime)
                .Select(s => new {
                    id = s.Id,
                    name = s.Name,
                    startTime = s.StartTime,
                    endTime = s.EndTime,
                    SessionId = s.Id
                })
                .ToListAsync();

            return Ok(sessions);
        }

        [HttpGet("sessions/{id}/packets")]
        public async Task<IActionResult> GetSessionPackets(int id)
        {
            using var scope = _services.CreateScope();
            var dbContext = _services.GetRequiredService<ApplicationContext>();

            var pactes = await dbContext.Packets
                .Where(p => p.SessionId == id)
                .OrderBy(p => p.Timestamp)
                .ToListAsync();
            return Ok(pactes);
        }

        [HttpPost("sessions/start")]
        public async Task<IActionResult> StartSession([FromBody] SessionRequest request)
        {
            _logger.LogInformation($"Создание сессии: {request.Name}");
            var sessionId = await _telemetryService.StartNewSession(request.Name);
            _logger.LogInformation($"Создана сессия ID: {sessionId}");
            return Ok(new { SessionId = sessionId });
        }

        [HttpPost("sessions/end")]
        public async Task<IActionResult> EndSession()
        {
            await _telemetryService.EndCurrentSession();
            return Ok();
        }

        public class SessionRequest
        {
            public string Name { get; set; }
        }

        public class StartRequest
        {
            public int? SessionId { get; set; }
        }

    }
}
