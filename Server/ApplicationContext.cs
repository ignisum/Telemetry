using Microsoft.EntityFrameworkCore;
using Server.Models;

namespace Server.Data
{
    public class ApplicationContext : DbContext
    {
        public DbSet<TelemetryPacket> Packets { get; set; }
        public DbSet<Session> Sessions { get; set; }

        public ApplicationContext(DbContextOptions<ApplicationContext> options) : base(options)
        {
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<TelemetryPacket>(entity =>
            {
                entity.ToTable("Packets");
                entity.Property(p => p.Id).ValueGeneratedOnAdd();
                entity.Property(p => p.Crc16).HasColumnType("smallint");
                entity.Property(p => p.SyncMarker).HasColumnType("bigint");
                entity.Property(p => p.PacketCounter).HasColumnType("bigint");
            });

            modelBuilder.Entity<Session>(entity => 
            {
                entity.ToTable("Sessions");
                entity.Property(s => s.Id).ValueGeneratedOnAdd();
                entity.Property(s => s.Name).HasMaxLength(256);
            });
        }
    }
}