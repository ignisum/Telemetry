using System.ComponentModel.DataAnnotations;

namespace Server.Models
{
    public class TelemetryPacket
    {
        [Key]
        public int Id { get; set; }
        public ushort Crc16 { get; set; }
        public uint PacketCounter { get; set; }
        public double Payload { get; set; }
        public uint SyncMarker { get; set; } = 0x12345678;
        public double Timestamp { get; set; }
    }
}