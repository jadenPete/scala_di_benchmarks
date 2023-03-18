#!/usr/bin/env python

import collections
import generator
import matplotlib
import matplotlib.pyplot as plot
import numpy as np
import os
import subprocess
import time

source_directory = os.path.dirname(os.path.realpath(__file__))

figure, axes = plot.subplots(2, 2)

def subplot(type_):
	return {
		generator.GeneratedType.MANUAL: axes[0, 0],
		generator.GeneratedType.IMPLICIT: axes[0, 1],
		generator.GeneratedType.MACWIRE: axes[1, 0],
		generator.GeneratedType.JAM: axes[1, 1]
	}[type_]

for type_, title in [
	(generator.GeneratedType.MANUAL, "Manual dependency injection"),
	(generator.GeneratedType.IMPLICIT, "Dependency injection with implicit parameter constructors"),
	(generator.GeneratedType.MACWIRE, "Dependency injection with MacWire"),
	(generator.GeneratedType.JAM, "Dependency injection with Jam")
]:
	subplot_ = subplot(type_)
	subplot_.grid()
	subplot_.set_title(title, fontsize=8)
	subplot_.set_xlabel("Base-10 logarithm of the number of injectables", fontsize=8)
	subplot_.set_ylabel("Compilation time in seconds", fontsize=7)
	subplot_.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.5))

x, y = collections.defaultdict(list), collections.defaultdict(list)

for power in np.arange(1, 3.5, 0.25):
	number = int(10 ** power)

	for type_ in generator.GeneratedType:
		path = os.path.join(source_directory, "src", type_.value, "scala", "Main.scala")

		with open(path, "w") as file:
			file.write(generator.generate(type_, number))

		start = time.perf_counter()

		subprocess.check_call(["sbt", f"{type_.value}/compile"])

		end = time.perf_counter()

		x[type_].append(power)
		y[type_].append(end - start)

for type_ in generator.GeneratedType:
	type_x, type_y = x[type_], y[type_]

	degree = 1 if type_ in {generator.GeneratedType.MANUAL, generator.GeneratedType.IMPLICIT} else 2

	model = np.poly1d(np.polyfit(type_x, type_y, degree))

	polynomial_line = np.linspace(min(type_x), max(type_x), 100)

	subplot_ = subplot(type_)
	subplot_.scatter(type_x, type_y, color="#1f77b4", marker="o")
	subplot_.plot(polynomial_line, model(polynomial_line), color="#1f77b4")

figure.tight_layout()

plot.show()
