using DotNetEnv;
using Microsoft.AspNetCore.Builder;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Server.Data;
using Server.Hubs;
using Server.Services;
using System.Reflection;


var appLocation = AppDomain.CurrentDomain.BaseDirectory;
var envPath = Path.Combine(appLocation, ".env");
if (!File.Exists(envPath))
{
    envPath = Path.Combine(
    Directory.GetParent(Directory.GetCurrentDirectory())?.Parent?.FullName ?? string.Empty,
    ".env");
}

Console.WriteLine($"Ищем .env файл по пути: {envPath}");

if (File.Exists(envPath))
{
    Env.Load(envPath);
}
else
{
    Console.WriteLine("Файл .env не найден. Используются переменные окружения системы.");
}

var serverPort = Environment.GetEnvironmentVariable("SERVER_PORT") ?? "15233";
var dbHost = Environment.GetEnvironmentVariable("DB_HOST") ?? "localhost";
var dbPort = Environment.GetEnvironmentVariable("DB_PORT") ?? "5432";
var dbName = Environment.GetEnvironmentVariable("DB_NAME") ?? "Telemetry";
var dbUser = Environment.GetEnvironmentVariable("DB_USER") ?? "postgres";
var dbSchema = Environment.GetEnvironmentVariable("DB_SCHEMA") ?? "public";
var dbPassword = Environment.GetEnvironmentVariable("DB_PASSWORD");

var connectionString = $"Host={dbHost};Port={dbPort};Database={dbName};" +
                     $"Username={dbUser};Password={dbPassword};" +
                     $"SearchPath={dbSchema};SslMode=Prefer";

try
{
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
        options.UseNpgsql(connectionString));

    builder.Services.AddSignalR();
    builder.Services.AddSingleton<TelemetryService>();
    builder.Services.AddHostedService(provider =>
        provider.GetRequiredService<TelemetryService>());
    builder.Services.AddSingleton<TelemetryManagerService>();
    builder.Services.AddControllers();

    var app = builder.Build();

    app.UseCors("AllowAll");
    app.MapControllers();
    app.MapHub<TelemetryHub>("/telemetryhub");

    using (var scope = app.Services.CreateScope())
    {
        var db = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
        try
        {
            await db.Database.MigrateAsync();
            if (await db.Database.CanConnectAsync())
            {
                Console.WriteLine("Подключение к БД успешно");
            }
            else
            {
                Console.WriteLine("Нет подключения к БД!");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Ошибка БД: {ex.Message}");
        }
    }

    var url = $"http://*:{serverPort}";
    Console.WriteLine($"Сервер запущен на {url}");
    await app.RunAsync(url);
}
catch (Exception ex)
{
    Console.WriteLine($"Критическая ошибка: {ex}");
}