from core.utils.tasks import BaseTask


class TrainSeatFinder(BaseTask):
    @property
    def name(self) -> str:
        return "task1.3"

    @property
    def small_desc(self) -> str:
        return "Check seat availability and find closest available seat"

    @property
    def usage(self) -> str:
        return f"python manage.py {self.name} --carriage CARRIAGE(int) --seat SEAT(int)"


    def setup_arguments(self):
        self.parser.add_argument("--carriage", type=int, help="Carriage number to check")
        self.parser.add_argument("--seat", type=str, help="Seat name to check")

    def find_closest_seat(self, carriage_data: list, current_seat_name: str) -> str:
        current_index = next((i for i, seat in enumerate(carriage_data) 
                            if seat["seat_name"] == current_seat_name), -1)
        
        if current_index == -1:
            return None
        
        left = current_index - 1
        right = current_index + 1
        
        while left >= 0 or right < len(carriage_data):
            if right < len(carriage_data) and not carriage_data[right]["isTaken"]:
                return carriage_data[right]["seat_name"]
            if left >= 0 and not carriage_data[left]["isTaken"]:
                return carriage_data[left]["seat_name"]
            
            left -= 1
            right += 1
        
        return None


    def find_any_available_seat(self, data: dict, current_carriage: int):
        for carriage in sorted(data.keys()):
            if carriage == current_carriage:
                continue
            for seat in data[carriage]:
                if not seat["isTaken"]:
                    return carriage, seat["seat_name"]
        
        return None, None

    def run(self, args):
        data = {
            1: [
                { "seat_name": "a1", "isTaken": True },
                { "seat_name": "a2", "isTaken": False },
                { "seat_name": "a3", "isTaken": True },
                { "seat_name": "a4", "isTaken": True },
                { "seat_name": "a5", "isTaken": False },
            ],
            2: [
                { "seat_name": "b1", "isTaken": False },
                { "seat_name": "b2", "isTaken": False },
                { "seat_name": "b3", "isTaken": True },
                { "seat_name": "b4", "isTaken": False },
                { "seat_name": "b5", "isTaken": True },
            ],
            3: [
                { "seat_name": "c1", "isTaken": False },
                { "seat_name": "c2", "isTaken": True },
                { "seat_name": "c3", "isTaken": True },
                { "seat_name": "c4", "isTaken": True },
                { "seat_name": "c5", "isTaken": False },
            ],
        }

        if not args.carriage or not args.seat:
            print("Please provide both carriage and seat arguments")
            return

        carriage = args.carriage
        seat_name = args.seat.lower()

        if carriage not in data:
            print(f"Carriage {carriage} doesn't exist")
            return

        requested_seat = next((seat for seat in data[carriage] 
                             if seat["seat_name"] == seat_name), None)

        if not requested_seat:
            print(f"Seat {seat_name} doesn't exist in carriage {carriage}")
            return

        if not requested_seat["isTaken"]:
            print(f"Seat {seat_name} in carriage {carriage} is available!")
            return

        print(f"Seat {seat_name} in carriage {carriage} is already taken.")

        closest_seat = self.find_closest_seat(data[carriage], seat_name)
        if closest_seat:
            print(f"The closest available seat in carriage {carriage} is {closest_seat}")
            return

        print(f"No available seats in carriage {carriage}. Searching other carriages...")
        found_carriage, found_seat = self.find_any_available_seat(data, carriage)
        
        if found_seat:
            print(f"Found available seat {found_seat} in carriage {found_carriage}")
        else:
            print("No available seats found in any carriage")
