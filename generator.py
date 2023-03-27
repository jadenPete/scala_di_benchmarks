#!/usr/bin/env python

import argparse
import enum

class GeneratedType(enum.Enum):
	MANUAL = "manual"
	IMPLICIT = "implicit"
	MACWIRE = "macwire"
	JAM = "jam"
	CUSTOM = "custom"

def generate_component(type_, i):
	parameter_name = f"dependency{i}"
	parameter = "" if i == 0 else f"{parameter_name}: Dependency{i}"

	constructor_parameter_list = "" if parameter == "" else f"({parameter})"

	if type_ == GeneratedType.IMPLICIT:
		constructor_argument_list = "" if i == 0 else f"({parameter_name})"
		wire_parameter_list = "" if i == 0 else f"(implicit {parameter})"

		object = f"""

object Dependency{i + 1} {{
	def wire{wire_parameter_list} = new Dependency{i + 1}{constructor_argument_list}
}}"""
	else:
		object = ""

	return f"class Dependency{i + 1}{constructor_parameter_list}{object}\n"

def generate_components_classes(number):
	body = "".join(f"\tdef dependency{i + 1}: Dependency{i + 1}\n" for i in range(number))

	return f"""trait BaseComponents {{
{body}
}}

@wireComponents[BaseComponents]
class Components extends BaseComponents
"""

def generate_wire(type_, i):
	declaration = f"lazy val dependency{i + 1}: Dependency{i + 1} = "
	component_type = f"Dependency{i + 1}"

	if type_ == GeneratedType.MANUAL:
		wire_arguments = "" if i == 0 else f"dependency{i}"

		return f"{declaration}new {component_type}({wire_arguments})"

	if type_ == GeneratedType.IMPLICIT:
		return f"implicit {declaration}{component_type}.wire"

	macro = "wire" if type_ == GeneratedType.MACWIRE else "jam.brew"

	return f"{declaration}{macro}[{component_type}]"

def generate(type_, number):
	imports = "import com.softwaremill.macwire.wire\n\n" if type_ == GeneratedType.MACWIRE else ""
	components = "".join(f"{generate_component(type_, i)}\n" for i in range(number))

	if type_ == GeneratedType.CUSTOM:
		components_classes = f"{generate_components_classes(number)}\n"
		declarations = ""
		print_expression = f"(new Components).dependency{number}"
	else:
		components_classes = ""
		declarations = "".join(f"\t{generate_wire(type_, i)}\n" for i in range(number)) + "\n"
		print_expression = f"dependency{number}"

	return f"""{imports}{components}{components_classes}object Main {{
{declarations}\tdef main(args: Array[String]) = {{
		println({print_expression})
	}}
}}
"""

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="generator.py",
		description="Generate Scala code performing dependency injection."
	)

	parser.add_argument("type", help='One of "manual", "implicit", "macwire", "jam", or "custom"')
	parser.add_argument("-n", "--number",
		help="The number of components to wire",
		required=True,
		type=int
	)

	arguments = parser.parse_args()

	print(generate(GeneratedType(arguments.type), arguments.number), end="")
