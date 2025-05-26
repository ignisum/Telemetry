using Microsoft.AspNetCore.Builder;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Server.Data;
using Server.Hubs;
using Server.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyHeader()
              .AllowAnyMethod()
              .AllowAnyOrigin();
    });
});
builder.Services.AddDbContext<ApplicationContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("PostgreSQL")));
builder.Services.AddSignalR();
builder.Services.AddSingleton<TelemetryService>();
builder.Services.AddHostedService(provider => provider.GetRequiredService<TelemetryService>());
builder.Services.AddSingleton<TelemetryManagerService>();
builder.Services.AddControllers();

var app = builder.Build();

var logger = app.Services.GetRequiredService<ILogger<Program>>();

app.UseCors("AllowAll");
app.MapControllers();
app.MapHub<TelemetryHub>("/telemetryhub");

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
    try
    {
        await db.Database.MigrateAsync(); ;
        logger.LogInformation("Проверка состояния БД...");
        if (!await db.Database.CanConnectAsync())
        {
            logger.LogWarning("Нет подключения к БД!");
        }
        else
        {
            logger.LogInformation("Подключение к БД успешно");
        }
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Ошибка подключения к БД");
    }
}

logger.LogInformation("Сервер запущен на http://localhost:15233");
await app.RunAsync();