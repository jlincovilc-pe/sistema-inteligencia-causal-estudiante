# Adenda de contratos y evaluación — cohorte 2026-II

**Versión:** `contratos-2026.10`  
**Alcance:** sílabo, guía del profesor, labs canónicos, Serie B y trabajo final.

Esta adenda resuelve las equivalencias que pueden afectar la admisibilidad o la
calificación. La autoridad para la evaluación es, en este orden, el **sílabo
vigente**, esta adenda y la guía del proyecto con su rúbrica. La guía del
profesor explica cómo enseñarlo; la monografía y los labs explican el método y
proporcionan práctica. Una explicación del libro no crea por sí sola un
requisito adicional.

El Apéndice E de la monografía y cualquier rúbrica histórica se usan como
orientación para esta cohorte. Los puntos, filtros y recuperaciones vigentes
son los de `06_proyecto_final/rubrica_proyecto.md` y esta adenda.

## Equivalencias que sí están autorizadas

- El registro de una model card usa las clases `observable` y `no_observable`.
  `falsificable` sigue siendo una categoría didáctica para describir evidencia:
  en el registro se representa por la prueba y su resultado, sin inventar una
  tercera clase de esquema.
- ATE, CATE o valor de política son estimandos válidos si la decisión, la
  población y el objeto de incertidumbre están declarados. Un intervalo del
  pseudoresultado transformado o del CATE no se llama intervalo del efecto
  individual.
- HTTP y CLI son transportes equivalentes. Deben devolver el estimando elegido,
  su incertidumbre, metadatos de versión y una abstención fuera del soporte.
  La elección del transporte no suma ni resta puntos por sí misma.
  Si el bundle no puede calcular un intervalo válido para el valor de una
  policy, devuelve igualmente un objeto de incertidumbre con
  `estado: sin_cuantificacion_valida`, el objeto cubierto y su limitación; el
  `uplift_score` no se presenta como intervalo.
- Si el método es DML, la ficha declara la variante DML y los pliegues. Si el
  método es AIPW/IRM, declara ese método y su cross-fitting; no se exige llamar
  DML a un estimador distinto.
- Una sensibilidad solo cuenta como cuantificada cuando es compatible con el
  estimando, la escala y el diseño. Cuando no existe una cuantificación válida,
  la ficha puede registrar `sin_cuantificacion_valida`, la limitación y la fecha
  de revisión. Ese estado no se penaliza por sí mismo.

## Filtro y recuperación

El filtro separa `FORMATO` (schema, ruta, comando, nombre o hash corregible sin
cambiar cifras, estimando ni decisión) de `SUSTANCIA` (pregunta, estimando,
puerta, abstención o separación de `truth`). Solo `FORMATO` abre una ventana de
48 horas. La defensa no convierte una insuficiencia técnica en falta de
integridad: la autoría se juzga con la evidencia entregada y las preguntas
comparables de la defensa.

Tres ejemplos inválidos:

1. etiquetar un intervalo del CATE o pseudoresultado como `ITE`;
2. declarar un supuesto no observable como `verificado` solo porque pasa un CI;
3. usar una sensibilidad de escala E-value para un estimando continuo sin
   declarar la transformación y su límite.

## Evidencia de comprensión

La defensa incluye la pregunta: **«¿Qué cambio mínimo en la evidencia, la
población o el umbral de decisión haría que dejaras de recomendar esta
intervención?»**. La respuesta debe señalar el artefacto o cálculo que cambiaría
y el supuesto que dejaría de sostenerse. Esto forma parte de interpretación y
comunicación; no crea una entrega nueva ni puntos adicionales.
