class calculator:
    def add(self, a, b):
        return a + b
    def subtract(self, a, b):
        return a - b
    def multiply(self, a, b):
        return a * b
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    

if __name__ == "__main__":
    calc = calculator()
    print(calc.add(10, 5))        # Output: 15
    print(calc.subtract(10, 5))   # Output: 5
    print(calc.multiply(10, 5))   # Output: 50
    print(calc.divide(10, 5))     # Output: 2.0
    a = input("Enter first number: ")
    b = input("Enter second number: ")
    operation = input("Enter operation (+, -, *, /): ")
    match operation:
        case "+":
            print(calc.add(float(a), float(b)))
        case "-":
            print(calc.subtract(float(a), float(b)))
        case "*":
            print(calc.multiply(float(a), float(b)))
        case "/":
            try:
                print(calc.divide(float(a), float(b)))
            except ValueError as e:
                print(e)
        case _:
            print("Invalid operation")