#!/usr/bin/env python

import argparse
import enum

class GeneratedType(enum.Enum):
	MANUAL = "manual"
	IMPLICIT = "implicit"
	MACWIRE = "macwire"
	JAM = "jam"

def generate_component(type_, i):
	parameter_name = f"dependency{i}"
	parameter = "" if i == 0 else f"{parameter_name}: Dependency{i}"
	implicit_parameter_list = "" if i == 0 else f"(implicit {parameter}, dummy: DummyImplicit)"

	if type_ == GeneratedType.IMPLICIT and i > 0:
		body = f""" {{
	def this(){implicit_parameter_list} = this({parameter_name})
}}
"""
	else:
		body = ""

	return f"class Dependency{i + 1}({parameter}){body}\n"

def generate_wire(type_, i):
	declaration = f"lazy val dependency{i + 1} = "
	component_type = f"Dependency{i + 1}"

	if type_ == GeneratedType.MANUAL:
		wire_arguments = "" if i == 0 else f"dependency{i}"

		return f"{declaration}new {component_type}({wire_arguments})\n"

	if type_ == GeneratedType.IMPLICIT:
		return f"implicit {declaration}new {component_type}\n"

	macro = "wire" if type_ == GeneratedType.MACWIRE else "jam.brew"

	return f"{declaration}{macro}[{component_type}]\n"

def generate(type_, number):
	imports = "import com.softwaremill.macwire.wire\n\n" if type_ == GeneratedType.MACWIRE else ""
	components = "".join(generate_component(type_, i) for i in range(number)).rstrip("\n")
	wires = "".join(f"\t{generate_wire(type_, i)}" for i in range(number))

	return f"""{imports}{components}

object Main {{
{wires}
	def main(args: Array[String]) {{
		println(dependency{number})
	}}
}}
"""

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="generator.py",
		description="Generate Scala code performing dependency injection."
	)

	parser.add_argument("type", help='One of "manual", "implicit", "macwire", or "jam"')
	parser.add_argument("-n", "--number",
		help="The number of components to wire",
		required=True,
		type=int
	)

	arguments = parser.parse_args()

	print(generate(GeneratedType(arguments.type), arguments.number), end="")
