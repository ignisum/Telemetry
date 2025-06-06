﻿using Microsoft.EntityFrameworkCore;
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
            modelBuilder.HasDefaultSchema("public");

            modelBuilder.Entity<TelemetryPacket>(entity =>
            {
                entity.ToTable("Packets", "public");
                entity.Property(p => p.Id).UseIdentityAlwaysColumn();
                entity.Property(p => p.Crc16).HasColumnType("integer");
                entity.Property(p => p.SyncMarker).HasColumnType("integer");
                entity.Property(p => p.PacketCounter).HasColumnType("integer");
            });

            modelBuilder.Entity<Session>(entity => 
            {
                entity.ToTable("Sessions", "public");
                entity.Property(s => s.Id).UseIdentityAlwaysColumn();
                entity.Property(s => s.Name).HasMaxLength(256);
            });
        }
    }
}