from flask import Flask, request, jsonify, render_template
import math

app = Flask(__name__)

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def validate_base(base):
    base = int(base)
    if not 2 <= base <= 36:
        raise ValueError("Base must be between 2 and 36.")
    return base


def digit_value(char):
    return DIGITS.index(char)


def to_decimal(value, base):
    """Convert a signed integer/fractional number in base 2–36 to decimal."""
    base = validate_base(base)
    value = str(value).strip().upper()

    if not value:
        raise ValueError("Please enter a number.")

    sign = 1
    if value.startswith("-"):
        sign = -1
        value = value[1:]
    elif value.startswith("+"):
        value = value[1:]

    if not value or value.count(".") > 1:
        raise ValueError("Please enter a valid number.")

    int_part, dot, frac_part = value.partition(".")
    if not int_part and not frac_part:
        raise ValueError("Please enter a valid number.")

    result = 0.0
    for char in int_part:
        if char not in DIGITS or digit_value(char) >= base:
            raise ValueError(f"Invalid digit '{char}' for base {base}.")
        result = result * base + digit_value(char)

    place_value = base
    for char in frac_part:
        if char not in DIGITS or digit_value(char) >= base:
            raise ValueError(f"Invalid digit '{char}' for base {base}.")
        result += digit_value(char) / place_value
        place_value *= base

    result *= sign
    if not math.isfinite(result):
        raise ValueError("The number is too large to convert.")
    return result


def from_decimal(value, base, precision=8):
    """Convert a decimal number to base 2–36."""
    base = validate_base(base)

    if not math.isfinite(value):
        raise ValueError("The result is too large to convert.")

    negative = value < 0
    value = abs(value)
    int_part = int(value)
    frac_part = value - int_part

    if int_part == 0:
        result = "0"
    else:
        result = ""
        while int_part:
            result = DIGITS[int_part % base] + result
            int_part //= base

    fraction = ""
    for _ in range(precision):
        if frac_part < 1e-12:
            break
        frac_part *= base
        digit = int(frac_part)
        fraction += DIGITS[digit]
        frac_part -= digit

    if fraction:
        result += "." + fraction
    if negative and result != "0":
        result = "-" + result
    return result


def convert_base(number, to_base):
    """Convert a decimal integer to another base."""
    number = int(number)
    to_base = validate_base(to_base)

    if number == 0:
        return "0"

    sign = "-" if number < 0 else ""
    number = abs(number)
    result = ""

    while number:
        result = DIGITS[number % to_base] + result
        number //= to_base

    return sign + result


def explain_number(value, base):
    """Build detailed place-value steps for a number."""
    base = validate_base(base)
    value = str(value).strip().upper()

    sign = ""
    if value.startswith("-"):
        sign = "-"
        value = value[1:]
    elif value.startswith("+"):
        value = value[1:]

    if not value or value.count(".") > 1:
        raise ValueError("Please enter a valid number.")

    int_part, dot, frac_part = value.partition(".")
    if not int_part and not frac_part:
        raise ValueError("Please enter a valid number.")

    steps = []
    terms = []
    decimal_value = 0.0

    if int_part:
        for index, char in enumerate(int_part):
            if char not in DIGITS or digit_value(char) >= base:
                raise ValueError(f"Invalid digit '{char}' for base {base}.")
            digit = digit_value(char)
            power = len(int_part) - index - 1
            contribution = digit * (base ** power)
            decimal_value += contribution
            terms.append(f"{digit} × {base}^{power} = {contribution}")
            steps.append({
                "title": f"Integer digit: {char}",
                "content": (
                    f"Digit: {char} = {digit}\n"
                    f"Base: {base}\n"
                    f"Position exponent: {power}\n"
                    f"Calculation: {digit} × {base}^{power}\n"
                    f"Contribution: {contribution}"
                )
            })

    if frac_part:
        for index, char in enumerate(frac_part):
            if char not in DIGITS or digit_value(char) >= base:
                raise ValueError(f"Invalid digit '{char}' for base {base}.")
            digit = digit_value(char)
            power = -(index + 1)
            contribution = digit * (base ** power)
            decimal_value += contribution
            terms.append(f"{digit} × {base}^{power} = {contribution:.10g}")
            steps.append({
                "title": f"Fractional digit: {char}",
                "content": (
                    f"Digit: {char} = {digit}\n"
                    f"Base: {base}\n"
                    f"Position exponent: {power}\n"
                    f"Calculation: {digit} × {base}^{power}\n"
                    f"Contribution: {contribution:.10g}"
                )
            })

    if not int_part:
        steps.insert(0, {
            "title": "Integer part",
            "content": "There is no integer part before the radix point."
        })

    if not frac_part:
        steps.append({
            "title": "Fractional part",
            "content": "There is no fractional part after the radix point."
        })

    if sign == "-":
        decimal_value *= -1

    steps.append({
        "title": "Add the place values",
        "content": (
            f"Expansion: {' + '.join(terms) if terms else '0'}\n"
            f"Apply sign: {sign or '+'}\n"
            f"Decimal value: {decimal_value:.12g}"
        )
    })

    return decimal_value, steps


def explain_conversion(decimal_value, output_base):
    """Create interactive steps for converting decimal to the output base."""
    base = validate_base(output_base)
    steps = []

    if decimal_value == 0:
        return [{
            "title": "Result is zero",
            "content": f"0 in base 10 = 0 in base {base}."
        }]

    negative = decimal_value < 0
    absolute_value = abs(decimal_value)
    integer_part = int(absolute_value)
    fractional_part = absolute_value - integer_part

    if integer_part == 0:
        steps.append({
            "title": "Integer part",
            "content": "The integer part is 0."
        })
    else:
        n = integer_part
        remainders = []
        while n > 0:
            quotient, remainder = divmod(n, base)
            remainders.append(DIGITS[remainder])
            steps.append({
                "title": f"Divide {n} by {base}",
                "content": (
                    f"{n} ÷ {base} = {quotient} remainder {remainder}\n"
                    f"Remainder digit: {DIGITS[remainder]}\n"
                    "Keep dividing the quotient until it becomes 0."
                )
            })
            n = quotient

        steps.append({
            "title": "Read the remainders upward",
            "content": (
                "Read the remainders from the last division to the first:\n"
                + "".join(reversed(remainders))
            )
        })

    fraction_digits = ""
    if fractional_part > 1e-12:
        steps.append({
            "title": "Convert the fractional part",
            "content": (
                f"Fractional decimal part: {fractional_part:.10g}\n"
                f"Multiply the fraction by the target base ({base}) "
                "repeatedly. Each integer part becomes the next digit."
            )
        })

        fraction = fractional_part
        for index in range(8):
            fraction *= base
            digit = int(fraction)
            fraction_digits += DIGITS[digit]
            fraction -= digit
            steps.append({
                "title": f"Fraction multiplication {index + 1}",
                "content": (
                    f"Fraction × base = {fraction + digit:.10g} × {base} "
                    f"as processed\n"
                    f"Integer digit: {DIGITS[digit]} ({digit})\n"
                    f"Remaining fraction: {fraction:.10g}"
                )
            })
            if fraction < 1e-12:
                break

    integer_result = convert_base(integer_part, base)
    answer = integer_result
    if fraction_digits:
        answer += "." + fraction_digits
    if negative and answer != "0":
        answer = "-" + answer

    steps.append({
        "title": "Final answer",
        "content": (
            f"Decimal value: {decimal_value:.12g}\n"
            f"Output base: {base}\n"
            f"Converted answer: {answer}"
        )
    })
    return steps


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError("Invalid request. Please try again.")

        mode = data.get("mode")
        out_base = validate_base(data.get("out_base"))

        a, steps_a = explain_number(
            data.get("num1", ""),
            validate_base(data.get("base1"))
        )

        if mode == "convert":
            result = a
            steps = [{
                "title": "Step 1 — Convert input to decimal",
                "content": (
                    f"Input: {data.get('num1')} (base {data.get('base1')})\n"
                    f"Decimal value: {a:.12g}"
                )
            }]
            steps.extend(steps_a)
            steps.append({
                "title": "Step 2 — Convert to output base",
                "content": f"Convert {a:.12g} from decimal to base {out_base}."
            })
            steps.extend(explain_conversion(result, out_base))

        elif mode == "arithmetic":
            b, steps_b = explain_number(
                data.get("num2", ""),
                validate_base(data.get("base2"))
            )
            operator = data.get("operator")

            if operator == "+":
                result = a + b
                operation = f"{a:.12g} + {b:.12g} = {result:.12g}"
            elif operator == "-":
                result = a - b
                operation = f"{a:.12g} - {b:.12g} = {result:.12g}"
            elif operator == "*":
                result = a * b
                operation = f"{a:.12g} × {b:.12g} = {result:.12g}"
            elif operator == "/":
                if b == 0:
                    raise ValueError("Cannot divide by zero.")
                result = a / b
                if not math.isclose(result, round(result), abs_tol=1e-10):
                    raise ValueError(
                        "This calculator currently supports integer results "
                        "for division only."
                    )
                result = int(round(result))
                operation = f"{a:.12g} ÷ {b:.12g} = {result}"
            else:
                raise ValueError("Invalid operation.")

            steps = [{
                "title": "Step 1 — Convert operand A",
                "content": (
                    f"Input: {data.get('num1')} (base {data.get('base1')})\n"
                    f"Decimal value: {a:.12g}"
                )
            }]
            steps.extend(steps_a)
            steps.append({
                "title": "Step 2 — Convert operand B",
                "content": (
                    f"Input: {data.get('num2')} (base {data.get('base2')})\n"
                    f"Decimal value: {b:.12g}"
                )
            })
            steps.extend(steps_b)
            steps.append({
                "title": "Step 3 — Perform the operation",
                "content": operation
            })
            steps.append({
                "title": "Step 4 — Convert the result",
                "content": f"Convert {result} in decimal to base {out_base}."
            })
            steps.extend(explain_conversion(result, out_base))

        else:
            raise ValueError("Invalid calculator mode.")

        answer = from_decimal(result, out_base)
        return jsonify(success=True, result=answer, steps=steps)

    except (ValueError, TypeError, OverflowError, IndexError) as error:
        return jsonify(success=False, error=str(error)), 400


if __name__ == "__main__":
    app.run(debug=True)
