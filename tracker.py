import json
import os

class CarbonTracker:
    def __init__(self):
        # Emission factors (simplified)
        # Carbon footprint in kg CO2 per unit
        self.factors = {
            "electricity": 0.5,     # per kWh
            "gas": 2.0,             # per cubic meter
            "petrol": 2.3,          # per liter
            "meat": 15.0,           # per kg
            "flight_short": 150.0,  # per flight
            "public_transport": 0.05 # per km
        }
        self.data_file = "user_data.json"
        self.logs = self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        return []
                    return json.loads(content)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.logs, f, indent=4)

    def add_activity(self, activity_type, amount):
        if activity_type not in self.factors:
            return False, "Tipe aktivitas tidak valid."
        
        emission = amount * self.factors[activity_type]
        entry = {
            "type": activity_type,
            "amount": amount,
            "emission": emission
        }
        self.logs.append(entry)
        self._save_data()
        return True, emission

    def get_total_emissions(self):
        return sum(log['emission'] for log in self.logs)

    def get_summary(self):
        summary = {}
        for log in self.logs:
            t = log['type']
            summary[t] = summary.get(t, 0) + log['emission']
        return summary
