def calculate_alu_flags(val_a_str: str, val_b_str: str, operation: str, bits: int = 4) -> dict:
    """
    Вычисляет результат сложения или вычитания и возвращает состояние флагов АЛУ:
    ZF (Zero), SF (Sign), CF (Carry), OF (Overflow).
    """
    a = int(val_a_str, 2)
    b = int(val_b_str, 2)
    mask = (1 << bits) - 1

    if operation == "add":
        res_raw = a + b
        sign_a = (a >> (bits - 1)) & 1
        sign_b = (b >> (bits - 1)) & 1
        sign_res = ((res_raw & mask) >> (bits - 1)) & 1

        cf = 1 if res_raw > mask else 0
        of = 1 if (sign_a == sign_b) and (sign_a != sign_res) else 0
        op_name = "addition"

    elif operation == "sub":
        res_raw = a - b
        b_neg = ((~b) + 1) & mask
        sign_a = (a >> (bits - 1)) & 1
        sign_b_neg = (b_neg >> (bits - 1)) & 1
        sign_res = ((res_raw & mask) >> (bits - 1)) & 1

        cf = 1 if a < b else 0
        of = 1 if (sign_a == sign_b_neg) and (sign_a != sign_res) else 0
        op_name = "substraction"

    res_masked = res_raw & mask
    res_bin = f"{res_masked:0{bits}b}"

    zf = 1 if res_masked == 0 else 0
    sf = (res_masked >> (bits - 1)) & 1

    trace = (
        f"Executed {op_name} for {val_a_str} and {val_b_str} ({bits}-bit system).\n"
        f"Exact execution result: {res_bin}.\n"
        f"Calculated Hardware Flags: ZF={zf} (Zero Flag), SF={sf} (Sign Flag), "
        f"CF={cf} (Carry Flag), OF={of} (Overflow Flag)."
    )

    return {"result": res_bin, "flags": {"ZF": zf, "SF": sf, "CF": cf, "OF": of}, "trace": trace}


def execute_shift(val_str: str, shift_amount: int, shift_type: str) -> dict:
    """
    Выполняет сдвиг строки бит.
    Типы: 'logical_right', 'logical_left', 'arithmetic_right', 'rotate_right'
    """
    bits = len(val_str)
    if shift_amount >= bits:
        shift_amount = shift_amount % bits

    res_list = list(val_str)
    sign_bit = val_str[0]

    for _ in range(shift_amount):
        if shift_type == "logical_right":
            res_list = ["0"] + res_list[:-1]
        elif shift_type == "logical_left":
            res_list = res_list[1:] + ["0"]
        elif shift_type == "arithmetic_right":
            res_list = [sign_bit] + res_list[:-1]
        elif shift_type == "rotate_right":
            res_list = [res_list[-1]] + res_list[:-1]

    res_bin = "".join(res_list)
    trace = f"Executed operational shift '{shift_type}' on binary value {val_str} by {shift_amount} positions. Final calculation result: {res_bin}."
    return {"result": res_bin, "trace": trace}


def convert_hex(hex_str: str, word_bits: int) -> dict:
    """
    Парсер для строк памяти ROM. Перевод дампа памяти в бинарный вид.
    """
    try:
        int_value = int(hex_str, 16)
        res_bin = bin(int_value)[2:].zfill(word_bits)

        # Этот лог заставит Квена выглядеть гением схемотехники
        trace = (
            f"Converted HEX value '0x{hex_str}' from ROM/RAM storage into a {word_bits}-bit binary representation. "
            f"Decimal value: {int_value}. Resulting binary string: {res_bin}."
        )
        return {"result": res_bin, "trace": trace}

    except ValueError:
        trace = f"Hex conversion failed. Invalid hexadecimal string: '{hex_str}'."
        return {"result": "Error", "trace": trace}


def convert_twos_complement(val_str: str) -> int:
    """
    Переводит строку битов из дополнительного кода в int со знаком.
    """
    bits = len(val_str)
    val = int(val_str, 2)

    if val & (1 << (bits - 1)):
        val -= (1 << bits)

    return val


def convert_int_to_twos_complement(val: int, bits: int) -> str:
    """
    Переводит int в дополнительный код заданной разрядности.
    """
    mask = (1 << bits) - 1
    val_masked = val & mask

    return f"{val_masked:0{bits}b}"


def execute_mux(inputs: list, select_str: str) -> dict:
    """
    Принимает список входов (строк) и строку адресных бит.
    Возвращает значение выбранного входа и логирует процесс для модели
    """
    if not inputs:
        trace = "Executed multiplexer failed: The input list is empty."
        return {"result": "Error", "trace": trace}

    try:
        select_int = int(select_str, 2)
        result = inputs[select_int]
        inputs_str = ", ".join(inputs)

        trace = (
            f"Executed multiplexer operation. Input lines: [{inputs_str}]."
            f"Selected bits: '{select_str} converted to decimal index {select_int}.'"
            f"Successfully selected input at index {select_int}. Final result: {result}."
        )
        return {"result": result, "trace": trace}
    except IndexError:
        inputs_str = ", ".join(inputs)
        trace = (f"Executed multiplexer failed. Selected bits '{select_str}' (decimal {select_int})"
                 f"are out of bounds for the input lines [{inputs_str}. Output is in an Error state"
        )
        return {"result": "Error", "trace": trace}
    except ValueError:
        trace = f"Executed multiplexer failed. Invalid binary select string: '{select_str}'."
        return {"result": "Error", "trace": trace}


def execute_demux(input_val: str, select_str: str) -> dict:
    """
    Принимает 1 входной сигнал и адресные биты.
    Строит массив выходов, где нужный выход равен input_val, а остальные - 0.
    Логирует процесс для модели.
    """
    try:
        num_outputs = 2 ** len(select_str)
        select_int = int(select_str, 2)

        outputs = ["0"] * num_outputs
        outputs[select_int] = input_val

        outputs_str = ", ".join(outputs)
        trace =(
            f"Executed demultiplexer operation. Input value '{input_val}' was routed "
            f"via selected bits '{select_str}' (decimal index {select_int}) into a total of {num_outputs} output lines."
            f"Final state of all output lines: [{outputs_str}]"
        )
        return {"result": outputs, "trace": trace}
    except ValueError:
        trace = f"Executed demultiplexer failed. Invalid binary select string: '{select_str}'."
        return {"result": [], "trace": trace}


