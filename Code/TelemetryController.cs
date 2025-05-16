using Microsoft.AspNetCore.Mvc;
using Server.Services;

namespace Server.Controllers
{ 
    [ApiController]
    [Route("api/[controller]")]
    public class TelemetryController : ControllerBase
    {
        private readonly TelemetryService _telemetryService;

        public TelemetryController(TelemetryService telemetryService)
        {
            _telemetryService = telemetryService;
        }

        [HttpPost("start")]
        public IActionResult StartGeneration()
        {
            _telemetryService.StartGeneration();
            return Ok("Генерация данных запущена");
        }

        [HttpPost("stop")]
        public IActionResult StopGeneration()
        {
            _telemetryService.StopGeneration();
            return Ok("Генерация данных остановлена");
        }

        [HttpGet("status")]
        public IActionResult GetStatus() => Ok("Сервер работает");
    }
}
