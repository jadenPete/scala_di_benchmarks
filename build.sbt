lazy val sharedSettings = Seq(scalaVersion := "2.12.17")

lazy val manual = (project in file("src/manual/scala")).settings(sharedSettings)
lazy val `implicit` = (project in file("src/implicit/scala")).settings(sharedSettings)
lazy val macwire = (project in file("src/macwire/scala"))
  .settings(
    sharedSettings ++ Seq(
      libraryDependencies += "com.softwaremill.macwire" %% "macros" % "2.5.8" % "provided"
    )
  )

lazy val jam = (project in file("src/jam/scala"))
  .settings(
    sharedSettings ++ Seq(
      libraryDependencies += "com.github.yakivy" %% "jam-core" % "0.2.1"
    )
  )
