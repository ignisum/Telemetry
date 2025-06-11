
namespace Server.Services
{
    public class TelemetryManagerService
    {
        private readonly TelemetryService _telemetryService;
        public TelemetryManagerService(TelemetryService telemetryService)
            => _telemetryService = telemetryService;

        public void StartGeneration(long? sessionId)
            => _telemetryService.StartGeneration(sessionId ?? throw new ArgumentNullException(nameof(sessionId)));

        public async Task StopGeneration(long sessionId)
            => await _telemetryService.StopGeneration(sessionId);
    }
}