import re
from core.utils.tasks import BaseTask


class NumberExtractorTask(BaseTask):
    @property
    def name(self) -> str:
        return "task1.2"

    @property
    def small_desc(self) -> str:
        return "Extracts numbers from a string and categorizes them into float, odd, and even lists"

    @property
    def usage(self) -> str:
        return f"python manage.py {self.name} --input TEXT"

    def setup_arguments(self):
        self.parser.add_argument("--input", type=str, help="Input string containing numbers to extract")

    def run(self, args):
        input_string = args.input
        
        float_list = []
        odd_list = []
        even_list = []
        
        numbers = re.findall(r'\d*\.?\d+', input_string)
        
        for num in numbers:
            float_num = float(num)
            if float_num % 1 != 0:
                float_list.append(float_num)
            else:
                int_num = int(float_num)
                if int_num % 2 == 0:
                    even_list.append(int_num)
                else:
                    odd_list.append(int_num)
        
        # Print results
        print(f"Float numbers: {float_list}")
        print(f"Odd numbers: {odd_list}")
        print(f"Even numbers: {even_list}")