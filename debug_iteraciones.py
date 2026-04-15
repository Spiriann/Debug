"""
Debug script: Simulación de iteraciones del bot REMATRICULAUSAM
Basado en logs: 2026-04-15 16:53:37 - línea 12.23

El bot itera sobre vGlbListMateriasAprobRegistro usando:
    for i in range(len(vGlbListMateriasAprobRegistro))
"""

# ─── Datos capturados del log ────────────────────────────────────────────────

vGlbListMateriasAprobRegistro = [
    {
        'nombre': 'ESTADISTICA PARA LAS CIENCIAS SOCIALES Y HUMANAS II',
        'codigo': 'BPSV-09',
        'creditos': 3,
        'requisitos': 'BPSV-08',
        'estado_requisito': 'BPSV-08:Aprobado',
        'razon': 'Requisitos cumplidos',
        'codigo_requisito_bd': 'N/A',
        'descripcion_requisito_bd': 'Sin requisitos pendientes',
    },
    {
        'nombre': 'PSICOMETRIA BASICA',
        'codigo': 'BPSV-18',
        'creditos': 3,
        'requisitos': 'BPSV-08',
        'estado_requisito': 'BPSV-08:Aprobado',
        'razon': 'Requisitos cumplidos',
        'codigo_requisito_bd': 'N/A',
        'descripcion_requisito_bd': 'Sin requisitos pendientes',
    },
]

# ─── Simulación del for del bot (línea 12.23) ────────────────────────────────

print("=" * 60)
print(f"TOTAL de materias en lista: {len(vGlbListMateriasAprobRegistro)}")
print("=" * 60)

for vIndiceMateria in range(len(vGlbListMateriasAprobRegistro)):
    materia = vGlbListMateriasAprobRegistro[vIndiceMateria]

    print(f"\n>>> ITERACIÓN {vIndiceMateria + 1} de {len(vGlbListMateriasAprobRegistro)}")
    print(f"    vIndiceMateria     : {vIndiceMateria}")
    print(f"    Nombre             : {materia['nombre']}")
    print(f"    Código             : {materia['codigo']}")
    print(f"    Créditos           : {materia['creditos']}")
    print(f"    Requisito          : {materia['requisitos']}")
    print(f"    Estado requisito   : {materia['estado_requisito']}")
    print(f"    Razón              : {materia['razon']}")
    print(f"    Código BD          : {materia['codigo_requisito_bd']}")
    print(f"    Descripción BD     : {materia['descripcion_requisito_bd']}")
    print("-" * 60)

print("\nFin del for (línea 12.23)")
