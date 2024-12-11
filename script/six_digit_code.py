from elem import elemtoz


def genenerate_six_digit_code_pn(element, formatted_mass):
    capitalized_element = element.capitalize()
    z = elemtoz(capitalized_element)
    z_modified = f"{int(z) + 1:03}"

    product_six_digit_code = z_modified + formatted_mass
    return product_six_digit_code


def genenerate_six_digit_code_p2n(element, formatted_mass):
    capitalized_element = element.capitalize()
    z = elemtoz(capitalized_element)
    z_modified = f"{int(z) + 1:03}"
    formatted_mass_modified = f"{int(formatted_mass) - 1:03}"

    product_six_digit_code = z_modified + formatted_mass_modified
    return product_six_digit_code


def genenerate_six_digit_code_ppn(element, formatted_mass):
    capitalized_element = element.capitalize()
    z = elemtoz(capitalized_element)
    formatted_mass_modified = f"{int(formatted_mass) - 1:03}"

    product_six_digit_code = z + formatted_mass_modified
    return product_six_digit_code
