"""
Weather API Client
Handles communication with the weather API
"""

import requests
import json


class WeatherAPIClient:
    """Client for weather API interactions"""

    def __init__(self, api_url="https://api.responsible-nlp.net/weather.php"):
        """
        Initialize Weather API client

        Args:
            api_url: URL of the weather API
        """
        self.api_url = api_url

    def get_weather(self, place):
        """
        Get weather forecast for a location

        Args:
            place: Location name (e.g., "Marburg", "Frankfurt")

        Returns:
            dict: Weather data with forecast for 7 days
                  Format: {
                      "place": str,
                      "forecast": [
                          {
                              "day": str,
                              "temperature": {"min": int, "max": int},
                              "weather": str
                          },
                          ...
                      ]
                  }
        """
        try:
            # Make POST request with place parameter
            response = requests.post(
                self.api_url,
                data={"place": place},
                timeout=10
            )

            # Check if request was successful
            if response.status_code == 200:
                weather_data = response.json()
                print(f"Weather data retrieved for {place}")
                return weather_data
            else:
                print(f"Error fetching weather: HTTP {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("Weather API request timed out")
            return None
        except requests.exceptions.ConnectionError:
            print("Failed to connect to weather API")
            return None
        except json.JSONDecodeError:
            print("Invalid JSON response from weather API")
            return None
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return None

    def get_weather_for_day(self, place, day):
        """
        Get weather forecast for a specific day

        Args:
            place: Location name
            day: Day name (e.g., "monday", "tuesday", etc.) or "today"

        Returns:
            dict: Weather data for the specific day or None
        """
        weather_data = self.get_weather(place)

        if not weather_data or "forecast" not in weather_data:
            return None

        # Normalize day name
        day_lower = day.lower()

        # If "today", return first day in forecast
        if day_lower == "today":
            return weather_data["forecast"][0] if weather_data["forecast"] else None

        # Find the specific day
        for forecast in weather_data["forecast"]:
            if forecast["day"].lower() == day_lower:
                return forecast

        print(f"No forecast found for {day}")
        return None

    def check_weather_condition(self, place, day, condition):
        """
        Check if a specific weather condition will occur

        Args:
            place: Location name
            day: Day name
            condition: Weather condition to check (e.g., "rain", "snow")

        Returns:
            bool: True if condition will occur, False otherwise, None if error
        """
        day_weather = self.get_weather_for_day(place, day)

        if not day_weather:
            return None

        weather = day_weather.get("weather", "").lower()
        condition_lower = condition.lower()

        # Check if condition is in weather description
        return condition_lower in weather


# Available weather conditions (as per API spec)
WEATHER_CONDITIONS = [
    "clear sky",
    "few clouds",
    "scattered clouds",
    "broken clouds",
    "shower rain",
    "rain",
    "thunderstorm",
    "snow",
    "mist"
]


if __name__ == "__main__":
    # Test Weather API client
    print("Testing Weather API Client\n")

    client = WeatherAPIClient()

    # Test 1: Get weather for Marburg
    print("Test 1: Get weather for Marburg")
    weather = client.get_weather("Marburg")
    if weather:
        print(f"Place: {weather['place']}")
        for day_forecast in weather['forecast']:
            print(f"  {day_forecast['day']}: {day_forecast['weather']}, "
                  f"Temp: {day_forecast['temperature']['min']}-{day_forecast['temperature']['max']}°C")
    print()

    # Test 2: Get weather for specific day
    print("Test 2: Get weather for Thursday in Marburg")
    thursday = client.get_weather_for_day("Marburg", "thursday")
    if thursday:
        print(f"Thursday: {thursday['weather']}, "
              f"Temp: {thursday['temperature']['min']}-{thursday['temperature']['max']}°C")
    print()

    # Test 3: Check for rain
    print("Test 3: Will it rain on Friday in Marburg?")
    will_rain = client.check_weather_condition("Marburg", "friday", "rain")
    print(f"Rain on Friday: {will_rain}")
