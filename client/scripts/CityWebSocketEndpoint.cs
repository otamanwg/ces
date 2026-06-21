using System;

public static class CityWebSocketEndpoint
{
    public static string BuildUrl(string cityId, string playerToken, string baseUrl = "ws://127.0.0.1:8000")
    {
        if (string.IsNullOrEmpty(cityId) || string.IsNullOrEmpty(playerToken))
        {
            return "";
        }

        string trimmedBaseUrl = baseUrl.TrimEnd('/');
        string encodedCityId = Uri.EscapeDataString(cityId);
        string encodedToken = Uri.EscapeDataString(playerToken);
        return $"{trimmedBaseUrl}/ws/city/{encodedCityId}?token={encodedToken}";
    }
}
