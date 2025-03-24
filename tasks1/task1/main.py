from core.utils.tasks import BaseTask

class ArmstrongTask(BaseTask):
    @property
    def name(self) -> str:
        return "task1.1"

    @property
    def small_desc(self) -> str:
        return "Finds Armstrong numbers in a given range and their sum."
    
    @property
    def usage(self) -> str:
        return f"python manage.py {self.name} [--start START] [--end END] [--desc]"

    def setup_arguments(self):
        self.parser.add_argument("--start", type=int, default=9, help="Start of the range (default: 9)")
        self.parser.add_argument("--end", type=int, default=9999, help="End of the range (default: 9999)")

    def is_armstrong(self, number: int) -> bool:
        digits = list(map(int, str(number)))
        power = len(digits)
        return number == sum(d ** power for d in digits)

    def recursive_sum(self, numbers: list) -> int:
        if not numbers:
            return 0
        return numbers[0] + self.recursive_sum(numbers[1:])

    def find_armstrong_numbers(self, start: int, end: int) -> list:
        return [num for num in range(start, end + 1) if self.is_armstrong(num)]

    def run(self, args):
        armstrong_numbers = self.find_armstrong_numbers(args.start, args.end)
        total_sum = self.recursive_sum(armstrong_numbers)
        print("Armstrong numbers:", armstrong_numbers)
        print("Sum of Armstrong numbers:", total_sum)