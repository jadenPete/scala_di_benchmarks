#!/usr/bin/env python

import generator
import matplotlib.pyplot as plot
import os
import subprocess
import time

SAMPLE_SIZE = 6
TYPE_LABELS = {
	generator.GeneratedType.MANUAL: "Manual",
	generator.GeneratedType.IMPLICIT: "Implicit constructor",
	generator.GeneratedType.MACWIRE: "MacWire",
	generator.GeneratedType.JAM: "Jam",
	generator.GeneratedType.CUSTOM: "Custom linear time complexity macro"
}

source_directory = os.path.dirname(os.path.realpath(__file__))

for type_ in generator.GeneratedType:
	x, y = [], []

	for number in range(500, 3600, 100):
		path = os.path.join(source_directory, "src", type_.value, "scala", "Main.scala")

		with open(path, "w") as file:
			file.write(generator.generate(type_, number))

		total = 0

		for _ in range(SAMPLE_SIZE):
			start = time.perf_counter()

			subprocess.check_call(["sbt", f"{type_.value}/compile", "clean"])

			end = time.perf_counter()

			total += end - start

		x.append(number)
		y.append(total / SAMPLE_SIZE)

	plot.plot(x, y, label=TYPE_LABELS[type_])

plot.grid()
plot.legend()
plot.xlabel("Number of injectables", fontsize=8)
plot.ylabel("Compilation time (seconds)", fontsize=7)

plot.show()
