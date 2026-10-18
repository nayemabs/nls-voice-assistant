"""
Calendar API Client
Handles CRUD operations for calendar entries
"""

import requests
import json
from datetime import datetime
from dateutil import parser as date_parser


class CalendarAPIClient:
    """Client for calendar API interactions with full CRUD support"""

    def __init__(self, api_url="https://api.responsible-nlp.net/calendar.php", calenderid="nayem_marburg_2026"):
        """
        Initialize Calendar API client

        Args:
            api_url: URL of the calendar API
            calenderid: Unique calendar ID for the team to avoid data interference
        """
        self.api_url = api_url
        self.calenderid = calenderid

    # CREATE operation
    def create_appointment(self, title, start_time, end_time,
                          description=None, location=None):
        """
        Create a new calendar appointment

        Args:
            title: Appointment title
            start_time: Start time (ISO format string or datetime object)
            end_time: End time (ISO format string or datetime object)
            description: Optional description
            location: Optional location

        Returns:
            dict: Created appointment data with ID, or None if failed
        """
        try:
            # Convert datetime objects to ISO format strings
            if isinstance(start_time, datetime):
                start_time = start_time.strftime("%Y-%m-%dT%H:%M")
            if isinstance(end_time, datetime):
                end_time = end_time.strftime("%Y-%m-%dT%H:%M")

            # Clean title - remove trailing periods
            title = title.strip().strip('.')

            # Build appointment data
            appointment_data = {
                "title": title,
                "start_time": start_time,
                "end_time": end_time
            }

            if description:
                appointment_data["description"] = description
            if location:
                appointment_data["location"] = location

            # Make POST request with calendar ID
            response = requests.post(
                f"{self.api_url}?calenderid={self.calenderid}",
                headers={"Content-Type": "application/json"},
                json=appointment_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Appointment created: {title}")
                return result
            else:
                print(f"Error creating appointment: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"Error creating appointment: {e}")
            return None

    # READ operations
    def get_all_appointments(self):
        """
        Get all calendar appointments

        Returns:
            list: List of all appointments, or None if failed
        """
        try:
            response = requests.get(f"{self.api_url}?calenderid={self.calenderid}", timeout=10)

            if response.status_code == 200:
                appointments = response.json()
                print(f"Retrieved {len(appointments)} appointments")
                return appointments
            else:
                print(f"Error fetching appointments: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching appointments: {e}")
            return None

    def get_appointment(self, appointment_id):
        """
        Get a specific appointment by ID

        Args:
            appointment_id: ID of the appointment

        Returns:
            dict: Appointment data, or None if not found
        """
        try:
            response = requests.get(
                f"{self.api_url}?calenderid={self.calenderid}&id={appointment_id}",
                timeout=10
            )

            if response.status_code == 200:
                appointment = response.json()
                print(f"Retrieved appointment: {appointment.get('title', 'N/A')}")
                return appointment
            else:
                print(f"Error fetching appointment: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching appointment: {e}")
            return None

    # UPDATE operation
    def update_appointment(self, appointment_id, **kwargs):
        """
        Update an existing appointment

        Args:
            appointment_id: ID of the appointment to update
            **kwargs: Fields to update (title, description, start_time, end_time, location)

        Returns:
            dict: Updated appointment data, or None if failed
        """
        try:
            # Filter out None values
            update_data = {k: v for k, v in kwargs.items() if v is not None}

            # Convert datetime objects to ISO format
            for time_field in ['start_time', 'end_time']:
                if time_field in update_data and isinstance(update_data[time_field], datetime):
                    update_data[time_field] = update_data[time_field].strftime("%Y-%m-%dT%H:%M")

            # Make PUT request with calendar ID
            response = requests.put(
                f"{self.api_url}?calenderid={self.calenderid}&id={appointment_id}",
                headers={"Content-Type": "application/json"},
                json=update_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Appointment {appointment_id} updated")
                return result
            else:
                print(f"Error updating appointment: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"Error updating appointment: {e}")
            return None

    # DELETE operation
    def delete_appointment(self, appointment_id):
        """
        Delete an appointment

        Args:
            appointment_id: ID of the appointment to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.api_url}?calenderid={self.calenderid}&id={appointment_id}",
                timeout=10
            )

            if response.status_code == 200:
                print(f"Appointment {appointment_id} deleted")
                return True
            else:
                print(f"Error deleting appointment: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"Error deleting appointment: {e}")
            return False

    # Helper methods
    def get_next_appointment(self):
        """
        Get the next upcoming appointment

        Returns:
            dict: Next appointment, or None if no upcoming appointments
        """
        appointments = self.get_all_appointments()

        if not appointments:
            return None

        now = datetime.now()
        upcoming = []

        for apt in appointments:
            try:
                start_time = date_parser.parse(apt['start_time'])
                if start_time > now:
                    upcoming.append((start_time, apt))
            except:
                continue

        if not upcoming:
            return None

        # Sort by start time and return the earliest
        upcoming.sort(key=lambda x: x[0])
        return upcoming[0][1]

    def get_appointments_by_date(self, target_date):
        """
        Get appointments for a specific date

        Args:
            target_date: Date to search (datetime object or string)

        Returns:
            list: Appointments on that date
        """
        appointments = self.get_all_appointments()

        if not appointments:
            return []

        # Parse target date if string
        if isinstance(target_date, str):
            target_date = date_parser.parse(target_date)

        matching = []
        for apt in appointments:
            try:
                start_time = date_parser.parse(apt['start_time'])
                if start_time.date() == target_date.date():
                    matching.append(apt)
            except:
                continue

        return matching


if __name__ == "__main__":
    # Test Calendar API client
    print("Testing Calendar API Client\n")

    client = CalendarAPIClient()

    # Test 1: Create appointment
    print("Test 1: Creating appointment")
    new_apt = client.create_appointment(
        title="Team Meeting",
        description="Discuss project progress",
        start_time="2025-11-03T09:00",
        end_time="2025-11-03T10:00",
        location="Room 12"
    )
    if new_apt:
        apt_id = new_apt.get('id')
        print(f"Created appointment with ID: {apt_id}\n")

        # Test 2: Get all appointments
        print("Test 2: Getting all appointments")
        all_apts = client.get_all_appointments()
        if all_apts:
            for apt in all_apts:
                print(f"  - {apt.get('title')} at {apt.get('start_time')}")
        print()

        # Test 3: Get specific appointment
        print(f"Test 3: Getting appointment {apt_id}")
        apt = client.get_appointment(apt_id)
        if apt:
            print(f"  Title: {apt.get('title')}")
            print(f"  Location: {apt.get('location')}")
        print()

        # Test 4: Update appointment
        print(f"Test 4: Updating appointment {apt_id}")
        updated = client.update_appointment(
            apt_id,
            location="Room 15",
            title="Updated Team Meeting"
        )
        print()

        # Test 5: Delete appointment
        print(f"Test 5: Deleting appointment {apt_id}")
        deleted = client.delete_appointment(apt_id)
        print(f"Deletion successful: {deleted}")
