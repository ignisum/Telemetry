
namespace Server.Services
{
    public class TelemetryManagerService
    {
        private readonly TelemetryService _telemetryService;
        public TelemetryManagerService(TelemetryService telemetryService)
            => _telemetryService = telemetryService;

        public void StartGeneration(int? sessionId)
            => _telemetryService.StartGeneration(sessionId);

        public void StopGeneration()
            => _telemetryService.StopGeneration();
    }
}
