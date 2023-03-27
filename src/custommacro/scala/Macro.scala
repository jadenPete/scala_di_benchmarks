import scala.annotation.{compileTimeOnly, StaticAnnotation}
import scala.language.experimental.macros
import scala.reflect.macros.whitebox

@compileTimeOnly("Macro annotations aren't supported by your version of Scala")
class wireComponents[T] extends StaticAnnotation {
	def macroTransform(annottees: Any*): Any = macro wireComponents.impl
}

object wireComponents {
	def buildCandidateMap(
		context: whitebox.Context
	)(componentsType: context.Type): Map[String, List[context.universe.TermName]] = {
		componentsType.members
			.filter { member =>
				member.isMethod &&
				member.asMethod.typeParams.isEmpty &&
				member.asMethod.paramLists.isEmpty &&
				!member.fullName.startsWith("java.lang.Object.") &&
				!member.fullName.startsWith("scala.Any.")
			}
			.map(_.asMethod)
			.flatMap { member =>
				member.returnType.dealias.baseClasses.map(_.fullName -> member.name)
			}
			.toList
			.groupMap(_._1)(_._2)
	}

	def getBaseMembers(
		context: whitebox.Context
	)(baseType: context.Type): List[context.universe.MethodSymbol] =
		baseType.members
			.filter { member =>
				member.isMethod && member.isAbstract && member.asMethod.paramLists.isEmpty
			}
			.map(_.asMethod)
			.toList

	def getBaseType(context: whitebox.Context): Option[context.Type] = {
		import context.universe._

		context.macroApplication match {
			case Apply(Select(Apply(Select(New(AppliedTypeTree(_, List(baseIdent: Ident))), _), _), _), _) => {
				val baseType = context.typecheck(baseIdent, mode = context.TYPEmode).tpe

				Some(baseType)
			}

			case _ => None
		}
	}

	/**
	  * Borrowed from
	  * https://github.com/yakivy/jam/blob/master/core/src-2/jam/core/JamMacro.scala#L167
	  */
	def getConstructorParameters(
		context: whitebox.Context
	)(injectableType: context.Type): List[List[context.Symbol]] = {
		val constructors = injectableType.members
            .filter(member => member.isMethod && member.isPublic)
			.map(_.asMethod)
            .filter { member =>
				member.isConstructor &&
				member.typeSignatureIn(injectableType).finalResultType =:= injectableType
			}

		if (constructors.isEmpty) {
			context.abort(
				context.enclosingPosition,
				s"Couldn't find a public constructor for $injectableType"
			)
		}

		val annotatedConstructors = constructors.filter {
			_.annotations.exists(_.tree.tpe.typeSymbol.fullName == "javax.inject.Inject")
		}

        val primaryConstructors =
			if (annotatedConstructors.isEmpty) constructors else annotatedConstructors

		primaryConstructors match {
			case List(constructor) => constructor.paramLists
			case _                 =>
				context.abort(
					context.enclosingPosition,
					s"Found more than one primary constructor for $injectableType"
				)
		}
	}

	def isSubtype(
		context: whitebox.Context
	)(classDef: context.universe.ClassDef, supertype: context.Type): Boolean = {
		import context.universe._

		context.typecheck(classDef).symbol.typeSignature.baseType(supertype.typeSymbol) != NoType
	}

	def parseAnnottees(
		context: whitebox.Context
	)(annottees: context.Expr[Any]*): Option[context.universe.ClassDef] = {
		import context.universe._

		annottees.headOption.map(_.tree) match {
			case Some(classDef: ClassDef) => Some(classDef)
			case _                        => None
		}

	}

	def wire(context: whitebox.Context)(
		classDef: context.universe.ClassDef,
		baseMembers: List[context.universe.MethodSymbol]
	): context.universe.ClassDef = {
		import context.universe._

		val classType = context.typecheck(classDef).symbol.typeSignature
		val candidateMap = buildCandidateMap(context)(classType)

		val overrides = baseMembers.map { member =>
			val memberType = member.returnType.dealias

			val constructorArguments =
				getConstructorParameters(context)(memberType).map {
					_.map { parameter =>
						val dependencyQualifier = parameter.typeSignature.typeSymbol.fullName

						candidateMap.get(dependencyQualifier).getOrElse(Nil) match {
							case _ :: _ :: _      =>
								context.abort(
									context.enclosingPosition,
									s"Found more than one injection candidate for $dependencyQualifier"
								)

							case candidateName :: Nil => q"$candidateName"
							case Nil              =>
								context.abort(
									context.enclosingPosition,
									s"Couldn't find an injection candidate for $dependencyQualifier"
								)
						}
					}
				}

			q"override lazy val ${member.name}: ${member.returnType} = new $memberType(...$constructorArguments)"
		}

		val q"$modifiers class $typeName[..$typeParameters] $constructorModifiers(...$parameters) extends { ..$earlyDefinitions } with ..$parents { $self => ..$statements }" =
			classDef

		q"""
		$modifiers class $typeName[..$typeParameters] $constructorModifiers(...$parameters)
			extends { ..$earlyDefinitions }
			with ..$parents { $self =>
			..$statements
			..$overrides
		}"""
	}

	def impl(context: whitebox.Context)(annottees: context.Expr[Any]*): context.Expr[Any] = {
		import context.universe._

		val baseType = getBaseType(context).getOrElse {
			context.abort(
				context.enclosingPosition,
				"wireComponents should be applied like `@wireComponents[T]`, where T is the base components type."
			)
		}

		val classDef = parseAnnottees(context)(annottees: _*).getOrElse {
			context.abort(
				context.enclosingPosition,
				"wireComponents should be applied to a class."
			)
		}

		if (!isSubtype(context)(classDef, baseType)) {
			context.abort(
				context.enclosingPosition,
				"The class to which wireComponents is applied should be a subclass of the base components type."
			)
		}

		context.Expr(wire(context)(classDef, getBaseMembers(context)(baseType)))
	}
}
