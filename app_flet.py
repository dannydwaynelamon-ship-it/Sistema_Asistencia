import asyncio
import time
from datetime import datetime
import flet as ft
import asistencia


async def main(page: ft.Page):
    page.title = "Sistema de Gestión Institucional - Pro Max"
    page.window.width = 1150
    page.window.height = 750
    page.window.resizable = False
    page.window.maximizable = False
    await page.window.center()
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F8FAFC"

    asistencia.inicializar_bd()

    sesion_usuario = {"rol": None, "año": 0, "activo": False}
    contenido_principal = ft.Container(expand=True, padding=20, bgcolor="#F8FAFC")

    # ==========================================
    # Cierre de sesión automático por inactividad (5 min)
    # ==========================================
    ultimo_movimiento = time.time()
    app_activa = True

    def registrar_actividad(e=None):
        nonlocal ultimo_movimiento
        ultimo_movimiento = time.time()

    def al_cerrar(e=None):
        nonlocal app_activa
        app_activa = False

    page.on_keyboard_event = registrar_actividad
    page.on_close = al_cerrar

    async def verificar_inactividad():
        while app_activa:
            await asyncio.sleep(10)
            if not app_activa:
                break
            if sesion_usuario["activo"]:
                if time.time() - ultimo_movimiento > 300:
                    sesion_usuario["activo"] = False
                    asistencia.registrar_auditoria(
                        sesion_usuario["rol"],
                        "Cierre de sesión automático por inactividad.",
                    )
                    try:
                        page.clean()
                        page.add(pantalla_login)
                        page.update()
                    except Exception:
                        break

    page.run_task(verificar_inactividad)

    def construir_interfaz_principal():
        pass

    # ==========================================
    # 1. PANTALLA DE LOGIN
    # ==========================================
    borde_login = {
        ft.ControlState.DEFAULT: ft.OutlineInputBorder(
            side=ft.BorderSide(color="#CBD5E1")
        ),
        ft.ControlState.FOCUSED: ft.OutlineInputBorder(
            side=ft.BorderSide(color="#2563EB")
        ),
    }

    dd_rol_login = ft.Dropdown(
        label="Seleccionar Departamento / Coordinación",
        width=420,
        height=52,
        filled=True,
        fill_color="#FFFFFF",
        bgcolor="#FFFFFF",
        border=borde_login,
        options=[
            ft.DropdownOption("0", text="🔑 Administrador General (Todos los Años)"),
            ft.DropdownOption("1", text="📚 Coordinación de 1er Año"),
            ft.DropdownOption("2", text="📚 Coordinación de 2do Año"),
            ft.DropdownOption("3", text="📚 Coordinación de 3er Año"),
            ft.DropdownOption("4", text="📚 Coordinación de 4to Año"),
            ft.DropdownOption("5", text="📚 Coordinación de 5to Año"),
            ft.DropdownOption("6", text="📚 Coordinación de 6to Año"),
        ],
    )

    txt_password = ft.TextField(
        label="Contraseña de Acceso",
        password=True,
        can_reveal_password=True,
        width=420,
        height=52,
        filled=True,
        bgcolor="#FFFFFF",
        border=borde_login,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
    )

    lbl_error_login = ft.Text(
        value="", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD, size=13
    )

    def iniciar_sesion(e):
        nonlocal ultimo_movimiento
        if not dd_rol_login.value or not txt_password.value:
            lbl_error_login.value = "⚠️ Por favor, completa todos los campos."
            page.update()
            return

        año_sel = int(dd_rol_login.value)
        clave = txt_password.value

        if asistencia.verificar_login(año_sel, clave):
            sesion_usuario["año"] = año_sel
            sesion_usuario["rol"] = (
                "Administrador General"
                if año_sel == 0
                else f"Coordinación de {año_sel}° Año"
            )
            sesion_usuario["activo"] = True
            ultimo_movimiento = time.time()
            txt_password.value = ""
            lbl_error_login.value = ""
            construir_interfaz_principal()
        else:
            lbl_error_login.value = "❌ Contraseña incorrecta. Intento registrado."
            page.update()

    btn_login = ft.Button(
        content="Ingresar al Sistema",
        icon=ft.Icons.LOGIN_ROUNDED,
        bgcolor="#2563EB",
        color=ft.Colors.WHITE,
        width=420,
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=iniciar_sesion,
    )

    card_login = ft.Card(
        elevation=8,
        bgcolor="#FFFFFF",
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=40, color="#FFFFFF"),
                                ft.Text(
                                    "Control de Asistencia Institucional",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color="#FFFFFF",
                                ),
                                ft.Text(
                                    "Plataforma de Gestión Educativa Pro Max",
                                    size=11,
                                    color="#94A3B8",
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6,
                        ),
                        bgcolor="#0F172A",
                        padding=25,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                dd_rol_login,
                                txt_password,
                                ft.Container(height=5),
                                btn_login,
                                lbl_error_login,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=14,
                        ),
                        padding=30,
                    ),
                ],
                spacing=0,
            ),
            width=500,
            bgcolor="#FFFFFF",
            border_radius=10,
        ),
    )

    pantalla_login = ft.Container(
        content=card_login,
        alignment=ft.Alignment.CENTER,
        expand=True,
        bgcolor="#F8FAFC",
    )

    # ==========================================
    # 2. VISTAS DEL DASHBOARD PRO MAX
    # ==========================================

    def vista_resumen():
        alumnos, profesores, asistencias = asistencia.obtener_estadisticas(
            sesion_usuario["año"]
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"Panel Principal - {sesion_usuario['rol']}",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#0F172A",
                    ),
                    ft.Text(
                        "Resumen general del estado actual de la institución.",
                        color="#64748B",
                        size=13,
                    ),
                    ft.Divider(height=20, color="#E2E8F0"),
                    ft.Row(
                        [
                            ft.Card(
                                elevation=2,
                                bgcolor="#FFFFFF",
                                content=ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.Icons.SCHOOL,
                                                        color="#2563EB",
                                                        size=26,
                                                    ),
                                                    ft.Text(
                                                        "Alumnos Activos",
                                                        size=15,
                                                        weight=ft.FontWeight.BOLD,
                                                        color="#1E293B",
                                                    ),
                                                ]
                                            ),
                                            ft.Text(
                                                str(alumnos),
                                                size=32,
                                                weight=ft.FontWeight.BOLD,
                                                color="#0F172A",
                                            ),
                                            ft.Text(
                                                "Matrícula registrada",
                                                size=11,
                                                color="#64748B",
                                            ),
                                        ]
                                    ),
                                    padding=22,
                                ),
                                expand=True,
                            ),
                            ft.Card(
                                elevation=2,
                                bgcolor="#FFFFFF",
                                content=ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.Icons.PERSON_PIN,
                                                        color="#0D9488",
                                                        size=26,
                                                    ),
                                                    ft.Text(
                                                        "Profesores Activos",
                                                        size=15,
                                                        weight=ft.FontWeight.BOLD,
                                                        color="#1E293B",
                                                    ),
                                                ]
                                            ),
                                            ft.Text(
                                                str(profesores),
                                                size=32,
                                                weight=ft.FontWeight.BOLD,
                                                color="#0F172A",
                                            ),
                                            ft.Text(
                                                "Docentes vinculados",
                                                size=11,
                                                color="#64748B",
                                            ),
                                        ]
                                    ),
                                    padding=22,
                                ),
                                expand=True,
                            ),
                            ft.Card(
                                elevation=2,
                                bgcolor="#FFFFFF",
                                content=ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.Icons.ASSIGNMENT,
                                                        color="#D97706",
                                                        size=26,
                                                    ),
                                                    ft.Text(
                                                        "Asistencias",
                                                        size=15,
                                                        weight=ft.FontWeight.BOLD,
                                                        color="#1E293B",
                                                    ),
                                                ]
                                            ),
                                            ft.Text(
                                                str(asistencias),
                                                size=32,
                                                weight=ft.FontWeight.BOLD,
                                                color="#0F172A",
                                            ),
                                            ft.Text(
                                                "Registros totales en BD",
                                                size=11,
                                                color="#64748B",
                                            ),
                                        ]
                                    ),
                                    padding=22,
                                ),
                                expand=True,
                            ),
                        ],
                        spacing=20,
                    ),
                    ft.Container(height=10),
                    ft.Card(
                        elevation=1,
                        bgcolor="#FFFFFF",
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.INFO_OUTLINE, color="#2563EB"
                                            ),
                                            ft.Text(
                                                "Control de Versiones y Auditoría de Usuario",
                                                weight=ft.FontWeight.BOLD,
                                                size=14,
                                            ),
                                        ]
                                    ),
                                    ft.Text(
                                        f"• Sesión activa registrada bajo: {sesion_usuario['rol']}\n"
                                        "• Cada cambio o modificación queda firmado en el historial de auditoría.",
                                        color="#64748B",
                                        size=12,
                                    ),
                                ],
                                spacing=8,
                            ),
                            padding=18,
                        ),
                    ),
                ],
                spacing=15,
            ),
            expand=True,
            bgcolor="#F8FAFC",
        )

    def vista_asistencia():
        # Pestaña 1: Registro Individual / Inasistencias
        txt_id = ft.TextField(
            label="ID del Miembro", width=380, height=48, filled=True, bgcolor="#FFFFFF"
        )
        txt_fecha = ft.TextField(
            label="Fecha (YYYY-MM-DD)",
            value=datetime.today().strftime("%Y-%m-%d"),
            width=380,
            height=48,
            filled=True,
            bgcolor="#FFFFFF",
        )
        dd_estado = ft.Dropdown(
            label="Estado",
            width=380,
            height=48,
            filled=True,
            fill_color="#FFFFFF",
            bgcolor="#FFFFFF",
            options=[
                ft.DropdownOption("PRESENTE"),
                ft.DropdownOption("AUSENTE"),
                ft.DropdownOption("JUSTIFICADO"),
            ],
        )
        dd_horas = ft.Dropdown(
            label="Horas de Estudio / Clase",
            width=380,
            height=48,
            filled=True,
            fill_color="#FFFFFF",
            bgcolor="#FFFFFF",
            value="1h",
            options=[
                ft.DropdownOption("1h"),
                ft.DropdownOption("2h"),
                ft.DropdownOption("3h"),
                ft.DropdownOption("4h"),
            ],
        )
        dd_materia = ft.Dropdown(
            label="Materia o Área",
            width=380,
            height=48,
            filled=True,
            fill_color="#FFFFFF",
            bgcolor="#FFFFFF",
            value="Matemáticas",
            options=[
                ft.DropdownOption("Matemáticas"),
                ft.DropdownOption("Lengua/Castellano"),
                ft.DropdownOption("Física"),
                ft.DropdownOption("Química"),
                ft.DropdownOption("Inglés"),
                ft.DropdownOption("General"),
            ],
        )
        txt_obs = ft.TextField(
            label="Observación (Opcional)",
            width=380,
            height=48,
            filled=True,
            bgcolor="#FFFFFF",
        )

        lbl_res_asist = ft.Text(value="", weight=ft.FontWeight.BOLD)
        lbl_info_persona = ft.Text(value="", italic=True, color="#2563EB")

        def verificar_id_en_vivo(e):
            if not txt_id.value:
                lbl_info_persona.value = ""
                page.update()
                return
            try:
                pid = int(txt_id.value)
                p = asistencia.obtener_persona_por_id(pid)
                if p:
                    lbl_info_persona.value = (
                        f"✔️ Encontrado: {p[2]} {p[3]} ({p[4]} - {p[5]}°{p[6]})"
                    )
                    lbl_info_persona.color = "#16A34A"
                else:
                    lbl_info_persona.value = "❌ No existe ningún registro con este ID."
                    lbl_info_persona.color = "#DC2626"
            except ValueError:
                lbl_info_persona.value = "⚠️ ID inválido."
                lbl_info_persona.color = "#D97706"
            page.update()

        txt_id.on_change = verificar_id_en_vivo

        def guardar_asist(e):
            if not txt_id.value or not dd_estado.value:
                lbl_res_asist.value = "⚠️ Faltan datos obligatorios."
                lbl_res_asist.color = ft.Colors.RED
                page.update()
                return
            exito, msg = asistencia.registrar_asistencia_avanzada(
                int(txt_id.value),
                txt_fecha.value,
                dd_estado.value,
                dd_horas.value,
                dd_materia.value,
                txt_obs.value,
                sesion_usuario["rol"],
            )
            lbl_res_asist.value = ("✅ " if exito else "❌ ") + msg
            lbl_res_asist.color = ft.Colors.GREEN if exito else ft.Colors.RED
            if exito:
                txt_id.value = ""
                txt_obs.value = ""
                lbl_info_persona.value = ""
                actualizar_lista_inasistencias()
            page.update()

        lista_inasistencias_view = ft.ListView(expand=1, spacing=8, padding=5)

        def actualizar_lista_inasistencias():
            lista_inasistencias_view.controls.clear()
            inasistencias = asistencia.obtener_inasistencias(sesion_usuario["año"])
            if not inasistencias:
                lista_inasistencias_view.controls.append(
                    ft.Text(
                        "No hay inasistencias registradas.",
                        italic=True,
                        color="#64748B",
                    )
                )
            else:
                for ina in inasistencias:
                    lista_inasistencias_view.controls.append(
                        ft.Card(
                            elevation=2,
                            bgcolor="#FFFFFF",
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            f"Fecha: {ina[7]}",
                                            width=105,
                                            weight=ft.FontWeight.BOLD,
                                            color="#DC2626",
                                        ),
                                        ft.Text(
                                            f"Cédula: {ina[1]}",
                                            width=100,
                                            color="#1E293B",
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            f"{ina[2]} {ina[3]}",
                                            width=170,
                                            color="#0F172A",
                                        ),
                                        ft.Container(
                                            content=ft.Text(
                                                f"Materia: {ina[9]}",
                                                size=11,
                                                color="#D97706",
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            bgcolor="#FEF3C7",
                                            padding=ft.Padding.symmetric(
                                                horizontal=8, vertical=4
                                            ),
                                            border_radius=5,
                                        ),
                                        ft.Text(
                                            f"Año: {ina[5]} | Sec: {ina[6]}",
                                            width=90,
                                            color="#64748B",
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                padding=12,
                            ),
                        )
                    )
            page.update()

        actualizar_lista_inasistencias()

        # Pestaña 2: Planilla Masiva por Sección (Checklist del Profesor)
        dd_masivo_anio = ft.Dropdown(
            label="Año Escolar",
            width=200,
            height=45,
            filled=True,
            fill_color="#FFFFFF",
            bgcolor="#FFFFFF",
            options=[
                ft.DropdownOption(str(i), text=f"{i}° Año") for i in range(1, 7)
            ],
            value=str(sesion_usuario["año"]) if sesion_usuario["año"] > 0 else "1",
        )
        dd_masivo_seccion = ft.Dropdown(
            label="Sección",
            width=150,
            height=45,
            filled=True,
            fill_color="#FFFFFF",
            bgcolor="#FFFFFF",
            options=[
                ft.DropdownOption("A"),
                ft.DropdownOption("B"),
                ft.DropdownOption("C"),
            ],
        )
        txt_masivo_fecha = ft.TextField(
            label="Fecha",
            value=datetime.today().strftime("%Y-%m-%d"),
            width=180,
            height=45,
            filled=True,
            bgcolor="#FFFFFF",
        )
        dd_masivo_materia = ft.Dropdown(
            label="Materia",
            width=200,
            height=45,
            filled=True,
            fill_color="#FFFFFF",
            bgcolor="#FFFFFF",
            value="Matemáticas",
            options=[
                ft.DropdownOption("Matemáticas"),
                ft.DropdownOption("Lengua/Castellano"),
                ft.DropdownOption("Física"),
                ft.DropdownOption("Química"),
                ft.DropdownOption("Inglés"),
                ft.DropdownOption("General"),
            ],
        )

        lista_planilla_view = ft.ListView(expand=1, spacing=6, padding=5)
        estados_planilla = {}  # Almacena el estado actual de cada checkbox de alumno

        def cargar_planilla_seccion(e):
            estados_planilla.clear()
            lista_planilla_view.controls.clear()
            try:
                an = int(dd_masivo_anio.value)
                sec = dd_masivo_seccion.value
                if not sec:
                    lista_planilla_view.controls.append(
                        ft.Text("⚠️ Seleccione una sección.", color=ft.Colors.RED)
                    )
                    page.update()
                    return
                alumnos = asistencia.obtener_alumnos_por_seccion(an, sec)
                if not alumnos:
                    lista_planilla_view.controls.append(
                        ft.Text(
                            "No hay alumnos registrados en esta sección.",
                            italic=True,
                            color="#64748B",
                        )
                    )
                else:
                    for al in alumnos:
                        # al = (id, cedula, nombre, apellido, año, seccion)
                        pid = al[0]
                        estados_planilla[pid] = "PRESENTE"  # Por defecto presente

                        # Controles de alternancia
                        btn_presente = ft.Button(
                            "Presente",
                            bgcolor="#16A34A",
                            color=ft.Colors.WHITE,
                            width=95,
                            height=32,
                        )
                        btn_ausente = ft.Button(
                            "Ausente",
                            bgcolor="#E2E8F0",
                            color="#1E293B",
                            width=95,
                            height=32,
                        )

                        def crear_selector(p_id, bp, ba):
                            def seleccionar_p(ev):
                                estados_planilla[p_id] = "PRESENTE"
                                bp.bgcolor = "#16A34A"
                                bp.color = ft.Colors.WHITE
                                ba.bgcolor = "#E2E8F0"
                                ba.color = "#1E293B"
                                bp.update()
                                ba.update()

                            def seleccionar_a(ev):
                                estados_planilla[p_id] = "AUSENTE"
                                ba.bgcolor = "#DC2626"
                                ba.color = ft.Colors.WHITE
                                bp.bgcolor = "#E2E8F0"
                                bp.color = "#1E293B"
                                bp.update()
                                ba.update()

                            bp.on_click = seleccionar_p
                            ba.on_click = seleccionar_a

                        crear_selector(pid, btn_presente, btn_ausente)

                        lista_planilla_view.controls.append(
                            ft.Card(
                                elevation=1,
                                bgcolor="#FFFFFF",
                                content=ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Text(
                                                f"V-{al[1]}",
                                                width=110,
                                                weight=ft.FontWeight.BOLD,
                                                color="#1E293B",
                                            ),
                                            ft.Text(
                                                f"{al[2]} {al[3]}",
                                                width=250,
                                                color="#0F172A",
                                            ),
                                            ft.Row(
                                                [btn_presente, btn_ausente], spacing=5
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                    padding=10,
                                ),
                            )
                        )
            except Exception as ex:
                lista_planilla_view.controls.append(
                    ft.Text(f"Error al cargar: {ex}", color=ft.Colors.RED)
                )
            page.update()

        btn_cargar_seccion = ft.Button(
            "Cargar Salón",
            icon=ft.Icons.SEARCH,
            bgcolor="#2563EB",
            color=ft.Colors.WHITE,
            on_click=cargar_planilla_seccion,
        )

        lbl_res_masivo = ft.Text(value="", weight=ft.FontWeight.BOLD)

        def guardar_asistencia_masiva(e):
            if not estados_planilla:
                lbl_res_masivo.value = "⚠️ Primero cargue y verifique el salón."
                lbl_res_masivo.color = ft.Colors.RED
                page.update()
                return

            fch = txt_masivo_fecha.value
            mat = dd_masivo_materia.value
            exitos = 0
            for pid, est in estados_planilla.items():
                ok, _ = asistencia.registrar_asistencia_avanzada(
                    pid,
                    fch,
                    est,
                    "1h",
                    mat,
                    "Planilla masiva del docente",
                    sesion_usuario["rol"],
                )
                if ok:
                    exitos += 1

            lbl_res_masivo.value = (
                f"✅ Asistencia registrada con éxito para {exitos} alumnos de la sección."
            )
            lbl_res_masivo.color = ft.Colors.GREEN
            actualizar_lista_inasistencias()
            page.update()

        btn_guardar_masivo = ft.Button(
            "Guardar Asistencia del Salón",
            icon=ft.Icons.SAVE_ROUNDED,
            bgcolor="#0D9488",
            color=ft.Colors.WHITE,
            height=42,
            on_click=guardar_asistencia_masiva,
        )

        tabs_asistencia = ft.Tabs(
            selected_index=0,
            length=3,
            expand=True,
            content=ft.Column(
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="📝 Registro Individual"),
                            ft.Tab(label="📋 Planilla del Profesor (Checklist Salón)"),
                            ft.Tab(label="❌ Inasistencias"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Divider(height=10),
                                        txt_id,
                                        lbl_info_persona,
                                        txt_fecha,
                                        dd_estado,
                                        dd_horas,
                                        dd_materia,
                                        txt_obs,
                                        ft.Button(
                                            "Guardar Asistencia",
                                            icon=ft.Icons.CHECK_ROUNDED,
                                            bgcolor="#2563EB",
                                            color=ft.Colors.WHITE,
                                            height=42,
                                            on_click=guardar_asist,
                                        ),
                                        lbl_res_asist,
                                    ],
                                    spacing=10,
                                    scroll=ft.ScrollMode.AUTO,
                                ),
                                padding=15,
                                bgcolor="#F8FAFC",
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Divider(height=10),
                                        ft.Row(
                                            [
                                                dd_masivo_anio,
                                                dd_masivo_seccion,
                                                txt_masivo_fecha,
                                                dd_masivo_materia,
                                                btn_cargar_seccion,
                                            ],
                                            spacing=10,
                                            wrap=True,
                                        ),
                                        ft.Divider(height=10),
                                        lista_planilla_view,
                                        ft.Row(
                                            [btn_guardar_masivo, lbl_res_masivo],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        ),
                                    ],
                                    expand=True,
                                    spacing=10,
                                ),
                                padding=15,
                                bgcolor="#F8FAFC",
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Divider(height=10),
                                        ft.Row(
                                            [
                                                ft.Text(
                                                    "Historial general de faltas",
                                                    size=13,
                                                    color="#64748B",
                                                ),
                                                ft.IconButton(
                                                    icon=ft.Icons.REFRESH_ROUNDED,
                                                    icon_color="#2563EB",
                                                    on_click=lambda e: actualizar_lista_inasistencias(),
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        ),
                                        lista_inasistencias_view,
                                    ],
                                    expand=True,
                                    spacing=8,
                                ),
                                padding=15,
                                bgcolor="#F8FAFC",
                            ),
                        ],
                    ),
                ],
                expand=True,
            ),
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Control Diario de Asistencia y Estudio",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#0F172A",
                    ),
                    tabs_asistencia,
                ],
                expand=True,
                spacing=10,
            ),
            expand=True,
            bgcolor="#F8FAFC",
        )

    def vista_gestion_personas():
        t_cedula = ft.TextField(
            label="Cédula", width=380, height=45, filled=True, bgcolor="#FFFFFF"
        )
        t_nombre = ft.TextField(
            label="Nombre", width=380, height=45, filled=True, bgcolor="#FFFFFF"
        )
        t_apellido = ft.TextField(
            label="Apellido", width=380, height=45, filled=True, bgcolor="#FFFFFF"
        )
        d_tipo = ft.Dropdown(
            label="Tipo",
            width=380,
            height=45,
            filled=True,
            fill_color="#FFFFFF",
            bgcolor="#FFFFFF",
            options=[
                ft.DropdownOption("ALUMNO"),
                ft.DropdownOption("PROFESOR"),
            ],
        )
        d_anio = ft.Dropdown(
            label="Año",
            width=380,
            height=45,
            filled=True,
            fill_color="#FFFFFF",
            bgcolor="#FFFFFF",
            options=[ft.DropdownOption(str(i)) for i in range(1, 7)],
        )
        t_seccion = ft.TextField(
            label="Sección (Ej: A, B)",
            width=380,
            height=45,
            filled=True,
            bgcolor="#FFFFFF",
        )
        lbl_res_reg = ft.Text(value="", weight=ft.FontWeight.BOLD)

        def registrar_click(e):
            if not all(
                [
                    t_cedula.value,
                    t_nombre.value,
                    t_apellido.value,
                    d_tipo.value,
                    d_anio.value,
                    t_seccion.value,
                ]
            ):
                lbl_res_reg.value = "⚠️ Completa todos los campos."
                lbl_res_reg.color = ft.Colors.RED
            else:
                exito = asistencia.registrar_persona(
                    t_cedula.value,
                    t_nombre.value,
                    t_apellido.value,
                    d_tipo.value,
                    int(d_anio.value),
                    t_seccion.value,
                    sesion_usuario["rol"],
                )
                if exito:
                    lbl_res_reg.value = "✅ ¡Registrado con éxito!"
                    lbl_res_reg.color = ft.Colors.GREEN
                    t_cedula.value = ""
                    t_nombre.value = ""
                    t_apellido.value = ""
                    t_seccion.value = ""
                    actualizar_listas()
                else:
                    lbl_res_reg.value = "❌ Error: Cédula duplicada."
                    lbl_res_reg.color = ft.Colors.RED
            page.update()

        btn_registrar = ft.Button(
            "Guardar Miembro",
            icon=ft.Icons.SAVE,
            bgcolor="#2563EB",
            color=ft.Colors.WHITE,
            height=42,
            on_click=registrar_click,
        )

        txt_buscar_alumnos = ft.TextField(
            label="🔍 Buscar Alumno por Cédula...",
            width=300,
            height=45,
            filled=True,
            bgcolor="#FFFFFF",
            on_change=lambda e: filtrar_alumnos(),
        )
        txt_buscar_profesores = ft.TextField(
            label="🔍 Buscar Profesor por Cédula...",
            width=300,
            height=45,
            filled=True,
            bgcolor="#FFFFFF",
            on_change=lambda e: filtrar_profesores(),
        )

        lista_alumnos_view = ft.ListView(expand=1, spacing=8, padding=5)
        lista_profesores_view = ft.ListView(expand=1, spacing=8, padding=5)

        cache_personas = []

        def actualizar_listas():
            nonlocal cache_personas
            cache_personas = asistencia.obtener_personas_por_coordinacion(
                sesion_usuario["año"]
            )
            filtrar_alumnos()
            filtrar_profesores()

        def abrir_modal_editar(p_id, p_ced, p_nom, p_ape, p_tip, p_an, p_sec):
            e_nom = ft.TextField(
                label="Nombre",
                value=p_nom,
                width=300,
                height=45,
                filled=True,
                bgcolor="#FFFFFF",
            )
            e_ape = ft.TextField(
                label="Apellido",
                value=p_ape,
                width=300,
                height=45,
                filled=True,
                bgcolor="#FFFFFF",
            )
            e_tip = ft.Dropdown(
                label="Tipo",
                value=p_tip,
                width=300,
                height=45,
                filled=True,
                fill_color="#FFFFFF",
                bgcolor="#FFFFFF",
                options=[
                    ft.DropdownOption("ALUMNO"),
                    ft.DropdownOption("PROFESOR"),
                ],
            )
            e_an = ft.Dropdown(
                label="Año",
                value=str(p_an),
                width=300,
                height=45,
                filled=True,
                fill_color="#FFFFFF",
                bgcolor="#FFFFFF",
                options=[ft.DropdownOption(str(i)) for i in range(1, 7)],
            )
            e_sec = ft.TextField(
                label="Sección",
                value=p_sec,
                width=300,
                height=45,
                filled=True,
                bgcolor="#FFFFFF",
            )

            def guardar_edicion(e):
                exito = asistencia.modificar_persona(
                    p_id,
                    e_nom.value,
                    e_ape.value,
                    e_tip.value,
                    int(e_an.value),
                    e_sec.value,
                    sesion_usuario["rol"],
                )
                if exito:
                    page.pop_dialog()
                    actualizar_listas()
                page.update()

            dlg_edit = ft.AlertDialog(
                title=ft.Text(f"Editar Registro ID: {p_id} (Cédula: {p_ced})"),
                content=ft.Column(
                    [e_nom, e_ape, e_tip, e_an, e_sec],
                    width=350,
                    height=300,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                    ft.Button(
                        "Guardar Cambios",
                        bgcolor="#2563EB",
                        color=ft.Colors.WHITE,
                        on_click=guardar_edicion,
                    ),
                ],
            )
            page.show_dialog(dlg_edit)

        def abrir_modal_eliminar(p_id, nombre_completo):
            def confirmar(e):
                asistencia.eliminar_persona(p_id, sesion_usuario["rol"])
                page.pop_dialog()
                actualizar_listas()
                page.update()

            dlg_del = ft.AlertDialog(
                title=ft.Text("⚠️ Confirmar Eliminación"),
                content=ft.Text(
                    f"¿Estás seguro de eliminar a {nombre_completo} (ID: {p_id})?"
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                    ft.Button(
                        "Sí, eliminar",
                        bgcolor="#DC2626",
                        color=ft.Colors.WHITE,
                        on_click=confirmar,
                    ),
                ],
            )
            page.show_dialog(dlg_del)

        def marcar_rapido(p_id, estado):
            fecha_hoy = datetime.today().strftime("%Y-%m-%d")
            asistencia.registrar_asistencia_avanzada(
                p_id,
                fecha_hoy,
                estado,
                "1h",
                "General",
                f"Marcado rápido por {sesion_usuario['rol']}",
                sesion_usuario["rol"],
            )
            page.show_dialog(
                ft.SnackBar(
                    ft.Text(
                        f"Asistencia [{estado}] guardada (Firmado por: {sesion_usuario['rol']})"
                    )
                )
            )

        def crear_fila_persona(p):
            p_id, ced, nom, ape, tip, an, sec = (
                p[0],
                p[1],
                p[2],
                p[3],
                p[4],
                p[5],
                p[6],
            )
            nom_comp = f"{nom} {ape}"

            def al_hacer_presente(e):
                marcar_rapido(p_id, "PRESENTE")

            def al_hacer_ausente(e):
                marcar_rapido(p_id, "AUSENTE")

            def al_hacer_editar(e):
                abrir_modal_editar(p_id, ced, nom, ape, tip, an, sec)

            def al_hacer_eliminar(e):
                abrir_modal_eliminar(p_id, nom_comp)

            badge_bg = "#EFF6FF" if tip == "ALUMNO" else "#F0FDFA"
            badge_color = "#2563EB" if tip == "ALUMNO" else "#0D9488"
            badge_text = f"{an}°{sec}" if tip == "ALUMNO" else "Docente"

            return ft.Card(
                elevation=2,
                bgcolor="#FFFFFF",
                content=ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                f"ID:{p_id}",
                                weight=ft.FontWeight.BOLD,
                                width=45,
                                color="#64748B",
                            ),
                            ft.Text(
                                f"V-{ced}",
                                width=90,
                                color="#1E293B",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(nom_comp, width=170, color="#0F172A"),
                            ft.Container(
                                content=ft.Text(
                                    badge_text,
                                    size=11,
                                    color=badge_color,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=badge_bg,
                                padding=4,
                                border_radius=5,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.CHECK_CIRCLE,
                                        icon_color="#16A34A",
                                        tooltip="Marcar Presente",
                                        icon_size=18,
                                        on_click=al_hacer_presente,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CANCEL,
                                        icon_color="#DC2626",
                                        tooltip="Marcar Ausente",
                                        icon_size=18,
                                        on_click=al_hacer_ausente,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        icon_color="#0D9488",
                                        tooltip="Editar",
                                        icon_size=18,
                                        on_click=al_hacer_editar,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color="#EF4444",
                                        tooltip="Eliminar",
                                        icon_size=18,
                                        on_click=al_hacer_eliminar,
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=8,
                ),
            )

        def filtrar_alumnos():
            lista_alumnos_view.controls.clear()
            filtro = (
                txt_buscar_alumnos.value.strip().lower()
                if txt_buscar_alumnos.value
                else ""
            )
            for p in cache_personas:
                if p[4] == "ALUMNO" and filtro in str(p[1]).lower():
                    lista_alumnos_view.controls.append(crear_fila_persona(p))
            page.update()

        def filtrar_profesores():
            lista_profesores_view.controls.clear()
            filtro = (
                txt_buscar_profesores.value.strip().lower()
                if txt_buscar_profesores.value
                else ""
            )
            for p in cache_personas:
                if p[4] == "PROFESOR" and filtro in str(p[1]).lower():
                    lista_profesores_view.controls.append(crear_fila_persona(p))
            page.update()

        actualizar_listas()

        sub_tabs = ft.Tabs(
            selected_index=0,
            length=3,
            expand=True,
            content=ft.Column(
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="🎓 Alumnos"),
                            ft.Tab(label="👨‍🏫 Profesores"),
                            ft.Tab(label="➕ Registrar Nuevo"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Divider(height=10),
                                        ft.Row(
                                            [
                                                txt_buscar_alumnos,
                                                ft.Text(
                                                    "💡 Control de versiones activo por usuario.",
                                                    size=11,
                                                    color="#64748B",
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        ),
                                        lista_alumnos_view,
                                    ],
                                    expand=True,
                                ),
                                padding=12,
                                bgcolor="#F8FAFC",
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Divider(height=10),
                                        ft.Row(
                                            [
                                                txt_buscar_profesores,
                                                ft.Text(
                                                    "💡 Control directo de personal.",
                                                    size=11,
                                                    color="#64748B",
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        ),
                                        lista_profesores_view,
                                    ],
                                    expand=True,
                                ),
                                padding=12,
                                bgcolor="#F8FAFC",
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Divider(height=10),
                                        t_cedula,
                                        t_nombre,
                                        t_apellido,
                                        d_tipo,
                                        d_anio,
                                        t_seccion,
                                        btn_registrar,
                                        lbl_res_reg,
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=10,
                                ),
                                padding=12,
                                bgcolor="#F8FAFC",
                            ),
                        ],
                    ),
                ],
                expand=True,
            ),
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"Directorio Institucional - {sesion_usuario['rol']}",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#0F172A",
                    ),
                    sub_tabs,
                ],
                expand=True,
                spacing=10,
            ),
            expand=True,
            bgcolor="#F8FAFC",
        )

    def vista_docentes_horas():
        t_doc_cedula = ft.TextField(
            label="Cédula Docente", width=320, height=45, filled=True, bgcolor="#FFFFFF"
        )
        t_doc_nombre = ft.TextField(
            label="Nombre y Apellido",
            width=320,
            height=45,
            filled=True,
            bgcolor="#FFFFFF",
        )
        t_doc_materia = ft.TextField(
            label="Materia / Área", width=320, height=45, filled=True, bgcolor="#FFFFFF"
        )
        lbl_res_doc = ft.Text(value="", weight=ft.FontWeight.BOLD)

        def guardar_docente(e):
            if not all([t_doc_cedula.value, t_doc_nombre.value, t_doc_materia.value]):
                lbl_res_doc.value = "⚠️ Completa todos los campos."
                lbl_res_doc.color = ft.Colors.RED
            else:
                exito, msg = asistencia.gestionar_docente(
                    t_doc_cedula.value,
                    t_doc_nombre.value,
                    t_doc_materia.value,
                    sesion_usuario["rol"],
                )
                lbl_res_doc.value = ("✅ " if exito else "❌ ") + msg
                lbl_res_doc.color = ft.Colors.GREEN if exito else ft.Colors.RED
                if exito:
                    t_doc_cedula.value = ""
                    t_doc_nombre.value = ""
                    t_doc_materia.value = ""
                    actualizar_docs()
            page.update()

        lista_docs_view = ft.ListView(expand=1, spacing=6, padding=5)

        def actualizar_docs():
            lista_docs_view.controls.clear()
            docs = asistencia.obtener_docentes()
            for d in docs:
                lista_docs_view.controls.append(
                    ft.Card(
                        elevation=2,
                        bgcolor="#FFFFFF",
                        content=ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(
                                        f"[{d[1]}]",
                                        weight=ft.FontWeight.BOLD,
                                        width=100,
                                        color="#1E293B",
                                    ),
                                    ft.Text(d[2], width=200, color="#0F172A"),
                                    ft.Text(f"Área: {d[3]}", width=150, color="#2563EB"),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_ROUNDED,
                                        icon_color="#DC2626",
                                        on_click=lambda e, did=d[0]: [
                                            asistencia.eliminar_docente(
                                                did, sesion_usuario["rol"]
                                            ),
                                            actualizar_docs(),
                                        ],
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            padding=10,
                        ),
                    )
                )
            page.update()

        actualizar_docs()

        tabs_doc = ft.Tabs(
            selected_index=0,
            length=1,
            expand=True,
            content=ft.Column(
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="👨‍🏫 Directorio de Docentes"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Divider(height=10),
                                        t_doc_cedula,
                                        t_doc_nombre,
                                        t_doc_materia,
                                        ft.Button(
                                            "Guardar Docente",
                                            icon=ft.Icons.SAVE,
                                            bgcolor="#0D9488",
                                            color=ft.Colors.WHITE,
                                            on_click=guardar_docente,
                                        ),
                                        lbl_res_doc,
                                        ft.Divider(height=10),
                                        ft.Text(
                                            "Plantilla Actual:",
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        lista_docs_view,
                                    ],
                                    expand=True,
                                    spacing=8,
                                    scroll=ft.ScrollMode.AUTO,
                                ),
                                padding=15,
                                bgcolor="#F8FAFC",
                            ),
                        ],
                    ),
                ],
                expand=True,
            ),
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Gestión Avanzada de Docentes",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#0F172A",
                    ),
                    tabs_doc,
                ],
                expand=True,
                spacing=10,
            ),
            expand=True,
            bgcolor="#F8FAFC",
        )

    def vista_excel_pdf():
        # Soporte para CSV y XLSX
        txt_ruta = ft.TextField(
            label="Ruta del archivo (.csv o .xlsx)",
            width=420,
            height=48,
            filled=True,
            bgcolor="#FFFFFF",
        )
        txt_id_pdf = ft.TextField(
            label="ID para Constancia PDF",
            width=420,
            height=48,
            filled=True,
            bgcolor="#FFFFFF",
        )
        lbl_msg = ft.Text(value="", weight=ft.FontWeight.BOLD)

        def importar_archivo(e):
            exito, msg = asistencia.importar_archivo_masivo(
                txt_ruta.value, sesion_usuario["rol"]
            )
            lbl_msg.value = msg
            lbl_msg.color = ft.Colors.GREEN if exito else ft.Colors.RED
            page.update()

        def exportar_xlsx(e):
            exito, msg = asistencia.exportar_a_archivo(
                "reporte_institucion.xlsx",
                sesion_usuario["año"],
                "xlsx",
                sesion_usuario["rol"],
            )
            lbl_msg.value = (
                "📥 Exportado como 'reporte_institucion.xlsx'" if exito else msg
            )
            lbl_msg.color = ft.Colors.GREEN if exito else ft.Colors.RED
            page.update()

        def exportar_csv(e):
            exito, msg = asistencia.exportar_a_archivo(
                "reporte_institucion.csv",
                sesion_usuario["año"],
                "csv",
                sesion_usuario["rol"],
            )
            lbl_msg.value = (
                "📥 Exportado como 'reporte_institucion.csv'" if exito else msg
            )
            lbl_msg.color = ft.Colors.GREEN if exito else ft.Colors.RED
            page.update()

        def pdf(e):
            if txt_id_pdf.value:
                exito, msg = asistencia.generar_constancia_pdf(
                    int(txt_id_pdf.value), f"Constancia_{txt_id_pdf.value}.pdf"
                )
                lbl_msg.value = "📄 PDF generado con éxito." if exito else msg
                lbl_msg.color = ft.Colors.GREEN if exito else ft.Colors.RED
                page.update()

        def promover_click(e):
            asistencia.promover_alumnos_institucion(sesion_usuario["rol"])
            lbl_msg.value = "🚀 ¡Alumnos promovidos de año escolar con éxito!"
            lbl_msg.color = ft.Colors.GREEN
            page.update()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Reportes, Promoción y Archivos CSV / XLSX",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#0F172A",
                    ),
                    ft.Text(
                        "Importa/Exporta en CSV o Excel, genera constancias PDF y administra períodos.",
                        color="#64748B",
                        size=13,
                    ),
                    ft.Divider(height=20),
                    ft.Row(
                        [
                            txt_ruta,
                            ft.Button(
                                "Importar CSV/XLSX",
                                icon=ft.Icons.UPLOAD_FILE,
                                bgcolor="#2563EB",
                                color=ft.Colors.WHITE,
                                on_click=importar_archivo,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.Button(
                                "Exportar a Excel (.xlsx)",
                                icon=ft.Icons.DOWNLOAD,
                                bgcolor="#0D9488",
                                color=ft.Colors.WHITE,
                                on_click=exportar_xlsx,
                            ),
                            ft.Button(
                                "Exportar a CSV (.csv)",
                                icon=ft.Icons.FILE_DOWNLOAD,
                                bgcolor="#4F46E5",
                                color=ft.Colors.WHITE,
                                on_click=exportar_csv,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Divider(height=10),
                    ft.Row(
                        [
                            txt_id_pdf,
                            ft.Button(
                                "Generar Constancia PDF",
                                icon=ft.Icons.PICTURE_AS_PDF,
                                bgcolor="#EA580C",
                                color=ft.Colors.WHITE,
                                on_click=pdf,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Divider(height=15),
                    ft.Text(
                        "Cierre de Período Académico",
                        weight=ft.FontWeight.BOLD,
                        size=15,
                    ),
                    ft.Button(
                        "Promover Alumnos al Siguiente Año",
                        icon=ft.Icons.UPDATE,
                        bgcolor="#D97706",
                        color=ft.Colors.WHITE,
                        on_click=promover_click,
                    ),
                    lbl_msg,
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            bgcolor="#F8FAFC",
            padding=20,
        )

    def vista_auditoria():
        # Control de Versiones / Historial de cambios por usuario
        lista_logs = ft.ListView(expand=1, spacing=8, padding=5)

        def cargar_logs():
            lista_logs.controls.clear()
            for l in asistencia.obtener_logs_auditoria():
                es_sospechoso = "FALLIDO" in l[2] or "SOSPECHOSO" in l[2]
                lista_logs.controls.append(
                    ft.Card(
                        elevation=2,
                        bgcolor="#FEF2F2" if es_sospechoso else "#FFFFFF",
                        content=ft.ExpansionTile(
                            title=ft.Row(
                                [
                                    ft.Text(f"[{l[3]}]", size=11, color="#64748B"),
                                    ft.Text(
                                        f"Usuario: {l[1]}",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color="#991B1B" if es_sospechoso else "#1E293B",
                                    ),
                                ],
                                spacing=10,
                            ),
                            subtitle=ft.Text(
                                l[2],
                                size=12,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        f"Acción registrada por el usuario [{l[1]}]:\n{l[2]}",
                                        size=12,
                                        color="#1E293B",
                                    ),
                                    padding=10,
                                    bgcolor="#F8FAFC",
                                )
                            ],
                        ),
                    )
                )
            page.update()

        cargar_logs()
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Control de Versiones y Auditoría de Cambios",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#0F172A",
                    ),
                    ft.Text(
                        "Historial exacto de qué modificaciones hizo cada usuario/coordinación y cuándo.",
                        color="#64748B",
                        size=13,
                    ),
                    ft.Button(
                        "Actualizar Historial",
                        icon=ft.Icons.REFRESH,
                        bgcolor="#0F172A",
                        color=ft.Colors.WHITE,
                        on_click=lambda e: cargar_logs(),
                    ),
                    lista_logs,
                ],
                expand=True,
                spacing=10,
            ),
            expand=True,
            bgcolor="#F8FAFC",
            padding=20,
        )

    # ==========================================
    # 3. INTERFAZ PRINCIPAL CON BARRA LATERAL PRO
    # ==========================================
    def construir_interfaz_principal():
        def ejecutar_logout():
            sesion_usuario["activo"] = False
            asistencia.registrar_auditoria(
                sesion_usuario["rol"], "Cerró sesión manualmente."
            )
            page.clean()
            page.add(pantalla_login)
            page.update()

        def confirmar_salida(e):
            def salir_confirmado(_):
                page.pop_dialog()
                ejecutar_logout()

            dlg = ft.AlertDialog(
                title=ft.Text("Cerrar Sesión"),
                content=ft.Text("¿Seguro que deseas salir?"),
                actions=[
                    ft.TextButton("No", on_click=lambda _: page.pop_dialog()),
                    ft.TextButton("Sí, salir", on_click=salir_confirmado),
                ],
            )
            page.show_dialog(dlg)

        def cambiar_vista(e):
            registrar_actividad()
            idx = e.control.selected_index
            if idx == 0:
                contenido_principal.content = vista_resumen()
            elif idx == 1:
                contenido_principal.content = vista_asistencia()
            elif idx == 2:
                contenido_principal.content = vista_gestion_personas()
            elif idx == 3:
                contenido_principal.content = vista_docentes_horas()
            elif idx == 4:
                contenido_principal.content = vista_excel_pdf()
            elif idx == 5:
                contenido_principal.content = vista_auditoria()
            elif idx == 6:
                confirmar_salida(e)
                return
            page.update()

        sidebar = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=110,
            min_extended_width=160,
            bgcolor="#0F172A",
            selected_label_text_style=ft.TextStyle(
                color="#FFFFFF", weight=ft.FontWeight.BOLD
            ),
            unselected_label_text_style=ft.TextStyle(color="#94A3B8"),
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD_ROUNDED,
                    label="Resumen",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.HOW_TO_REG_OUTLINED,
                    selected_icon=ft.Icons.HOW_TO_REG_ROUNDED,
                    label="Asistencia",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PEOPLE_OUTLINE,
                    selected_icon=ft.Icons.PEOPLE_ROUNDED,
                    label="Estudiantes",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PERSON_PIN_OUTLINED,
                    selected_icon=ft.Icons.PERSON_PIN,
                    label="Docentes",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                    selected_icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                    label="Reportes",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SECURITY_OUTLINED,
                    selected_icon=ft.Icons.SECURITY_ROUNDED,
                    label="Auditoría",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.LOGOUT_OUTLINED,
                    selected_icon=ft.Icons.LOGOUT_ROUNDED,
                    label="Salir",
                ),
            ],
            on_change=cambiar_vista,
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.SCHOOL_ROUNDED, color="#FFFFFF", size=22),
                            ft.Text(
                                "Sistema de Control de Asistencia - Colegio Pro Max",
                                color="#FFFFFF",
                                weight=ft.FontWeight.BOLD,
                                size=15,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.CIRCLE, color="#4ADE80", size=9),
                                ft.Text(
                                    f"Rol: {sesion_usuario['rol']}",
                                    color="#FFFFFF",
                                    size=12,
                                ),
                            ],
                            spacing=6,
                        ),
                        bgcolor="#1E293B",
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        border_radius=20,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor="#1E293B",
            padding=16,
        )

        contenido_principal.content = vista_resumen()

        layout = ft.Column(
            [
                header,
                ft.Row(
                    [
                        sidebar,
                        ft.VerticalDivider(width=1, color="#E2E8F0"),
                        contenido_principal,
                    ],
                    expand=True,
                    spacing=0,
                ),
            ],
            expand=True,
        )
        contenedor_interactivo = ft.GestureDetector(
            content=layout,
            on_hover=registrar_actividad,
            hover_interval=1000,
            expand=True,
        )
        page.clean()
        page.add(contenedor_interactivo)
        page.update()

    page.add(pantalla_login)


ft.run(main)
