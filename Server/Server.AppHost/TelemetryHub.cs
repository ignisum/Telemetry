using Microsoft.AspNetCore.SignalR;
using Server.Models;

namespace Server.Hubs
{
    public class TelemetryHub : Hub
    {
        public async Task SendPacket(TelemetryPacket packet)
        {
            await Clients.Group($"session-{packet.SessionId}").SendAsync("NewPacket", packet);
        }

        public async Task JoinSession(long sessionId)
        {
            Console.WriteLine($"Client {Context.ConnectionId} joining session {sessionId}");
            await Groups.AddToGroupAsync(Context.ConnectionId, $"session-{sessionId}");
            await Clients.Caller.SendAsync("SessionJoined", sessionId);
        }

        public async Task LeaveSession(long sessionId)
        {
            Console.WriteLine($"Client {Context.ConnectionId} leaving session {sessionId}");
            await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"session-{sessionId}");
            await Clients.Caller.SendAsync("SessionLeft", sessionId);
        }

        public override async Task OnConnectedAsync()
        {
            await base.OnConnectedAsync();
        }

        public override async Task OnDisconnectedAsync(Exception exception)
        {
            await base.OnDisconnectedAsync(exception);
        }
    }
}