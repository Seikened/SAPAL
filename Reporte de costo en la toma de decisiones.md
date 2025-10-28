# Reporte ejecutivo — Costo de la toma de decisiones directivas (SAPAL)

## Objetivo

Estimar cuánto dinero cuesta el tiempo invertido en **toma de decisiones** por el equipo directivo–técnico, bajo un supuesto operativo de 72 horas mensuales dedicadas a decidir, y proyectar el impacto financiero de mejoras en eficiencia operativa.

## Alcance

El análisis se centra en 22 cargos identificados como **roles críticos** dentro del organigrama de SAPAL.  
El interés no es exponer sueldos individuales, sino cuantificar el **costo del tiempo de decisión** por rol y modelar posibles escenarios de ahorro.

## Resultados clave

- Costo mensual del equipo analizado (72 h/mes): **$538,113 MXN**  
- Proyección a 5 años bajo el estado actual: **$32,286,787 MXN**  
- Total de trabajadores en nómina: **1,605**  
- Cargos críticos encontrados en la base: **22/22**

---

## Metodología

### Fuentes de datos

- **Organigrama**: roles jerárquicos obtenidos del portal oficial de SAPAL.  
- **Remuneraciones**: monto mensual bruto en tabulador (2023).  
- **Conversión temporal**: 4.33 semanas por mes y 48 horas por semana.  

### Supuestos base

1. 72 h/mes dedicadas a la toma de decisiones.  
2. Horizonte de análisis de 5 años.  
3. Escenarios de eficiencia del 25 %, 50 % y 75 %.  
4. Cálculos basados en salario bruto mensual.  

---

## Fórmulas utilizadas

### Sueldo semanal

$$
\text{sueldo\_semanal} = \frac{\text{salario\_bruto\_mensual}}{4.33}
$$

### Sueldo por hora

$$
\text{sueldo\_hora} = \frac{\text{salario\_bruto\_mensual}}{4.33 \times 48}
$$

### Costo mensual del tiempo de decisión

$$
C_{\text{mes}} = \sum(\text{sueldo\_hora}) \times \text{HORAS\_AL\_MES}
$$

donde  
**HORAS AL MES = 72**

### Costo anual proyectado a Y años

$$
C_{Y\text{ años}} = C_{\text{mes}} \times 12 \times Y
$$

### Costo acumulado sin ahorro (escenario base)

$$
C_{\text{sin ahorro}}(t) = C_{\text{anual}} \times t
$$

### Costo acumulado con ahorro (factor de eficiencia f)

$$
C_{\text{con ahorro}}(t) = C_{\text{anual}} \times (1 - f) \times t
$$

### Ahorro acumulado

$$
A(t) = C_{\text{sin ahorro}}(t) - C_{\text{con ahorro}}(t)
$$

### Costo restante proyectado

$$
R(t) = C_{\text{anual}} \times (T - t)
$$

### Punto de equilibrio (break-even)

$$
A(t) = R(t)
$$

---

## Interpretación

Las fórmulas permiten cuantificar el costo del tiempo de decisión y estimar el impacto financiero de **reducir tiempos de validación o mejorar procesos**.  
El análisis revela cómo pequeñas mejoras en eficiencia se traducen en **ahorros acumulados significativos** y en una **reducción del costo proyectado** a lo largo de los años.  

---

## Ejemplo de cálculo aplicado

**Costo mensual total del equipo (72 h/mes):**

$$
C_{\text{mes}} = \$538{,}113
$$

**Proyección a 5 años (sin ahorro):**

$$
C_{5\text{ años}} = \$32{,}286{,}787
$$

---

## Gráficas y visualizaciones

### Figura 1 — Costo mensual de decisión por rol (MXN)
Muestra qué funciones concentran el costo mensual de mantener el proceso de decisión.  
**Lectura**: los roles más altos generan mayor costo por minuto de indecisión.  
![[Pasted image 20251027221956.png]]

---

### Figura 2 — Factor de importancia relativo por rol (0–1)
Normaliza el peso de cada rol respecto al más costoso.  
**Lectura**: ayuda a identificar dónde una mejora operativa tiene mayor retorno.  
![[Pasted image 20251027222014.png]]

---

### Figura 3 — Reducción del costo restante vs. ahorro acumulado (escenario 50 %)
Muestra dos curvas opuestas: el **costo restante** (gris, decreciente) y el **ahorro acumulado** (verde, creciente).  
El punto donde se cruzan representa el **break-even**, cuando la eficiencia “se paga sola”.  
![[Pasted image 20251027222024.png]]

---

### Figura 4 — Ahorro acumulado por escenarios (25 %, 50 %, 75 %)
Compara los diferentes niveles de eficiencia a lo largo del tiempo.  
**Lectura**: a mayor eficiencia, mayor valor retenido.  
![[Pasted image 20251027222033.png]]

---

## Conclusión

El análisis muestra que la toma de decisiones directivas representa un costo recurrente y acumulativo.  
Implementar mejoras en eficiencia operativa permite **reducir costos futuros** y **acelerar el retorno de inversión**.  
El punto de equilibrio marca el momento en que el proyecto **se autofinancia**, generando ahorro neto a partir de ese año.

---

## Fuentes

- Organigrama SAPAL (jerarquía de roles):  
  https://www.sapal.gob.mx/organigrama  

- Remuneraciones brutas mensuales (tabulador, 2023):  
  https://www.sapal.gob.mx/documents/36855/136950/LTAIPG26F1_VIII+OCT-DIC.xlsx/fe0aaefd-dd33-7839-f11f-f507f9c7f53d?t=1706536909079  

**Fecha de referencia de los datos:** 2023
