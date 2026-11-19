# Curso: Programacion (213023) - Fase 4
# Grupo:360
# Empresa: Software FJ
# Modulo 1 - Daniel Esteban Zapata Abadia
# Modulo 2 - Jhojhan Yezid Meneses Ardila
# Modulo 3 - Victor Olmedo Tello Padilla
# Modulo 4 - (Daniel Esteban Zapata - Jhojhan Yezid Meneses Ardila - Victor Olmedo Tello Padilla)
# Modulo 5 - (Daniel Esteban Zapata - Jhojhan Yezid Meneses Ardila - Victor Olmedo Tello Padilla)

import math
import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime

# Modulo 1: CIMIENTOS, LOGS Y EXCEPCIONES

# gestor del archivo de logs para registrar eventos y errores sin detener el programa
class GestorLogs:
    archivo_log = "eventos_software_fj.log"

    @classmethod
    def registrar_evento(cls, tipo, mensaje):
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{fecha_hora}] [{tipo}] {mensaje}\n"
        try:
            with open(cls.archivo_log, "a", encoding="utf-8") as archivo:
                archivo.write(linea)
        except Exception as e:
            print(f"Error critico al escribir en el log: {e}")

    @classmethod
    def registrar_info(cls, mensaje):
        cls.registrar_evento("INFO", mensaje)

    @classmethod
    def registrar_error(cls, error, contexto=""):
        detalle = f"{contexto} -> {type(error).__name__}: {error}"
        # si hay encadenamiento de excepciones (__cause__), tambien lo guarda en el log
        if error.__cause__:
            detalle += f" | Causa original: {type(error.__cause__).__name__}: {error.__cause__}"
        cls.registrar_evento("ERROR", detalle)


# excepciones personalizadas para el sistema
class SoftwareFJError(Exception):
    """Clase base para todas las excepciones personalizadas del sistema."""
    pass

class DatosInvalidosError(SoftwareFJError):
    """Se lanza cuando los datos de un cliente o parametro son incorrectos o faltan."""
    pass

class ServicioNoDisponibleError(SoftwareFJError):
    """Se lanza cuando un servicio no existe, no tiene cupo o sus parametros fallan."""
    pass

class ReservaInvalidaError(SoftwareFJError):
    """Se lanza cuando hay errores al confirmar, cancelar o procesar una reserva."""
    pass

class CalculoInconsistenteError(SoftwareFJError):
    """Se lanza cuando un calculo de costo, descuento o duracion da valores invalidos."""
    pass


# clase abstracta general para todas las entidades del sistema
class EntidadSistema(ABC):
    def __init__(self, id_entidad):
        if not id_entidad or str(id_entidad).strip() == "":
            error = DatosInvalidosError("El identificador (ID) de la entidad no puede estar vacio.")
            GestorLogs.registrar_error(error, "Creacion de EntidadSistema")
            raise error
        self._id_entidad = str(id_entidad).strip()
        self._fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def id_entidad(self):
        return self._id_entidad

    @property
    def fecha_creacion(self):
        return self._fecha_creacion

    # metodos abstractos que obligan a las clases hijas (Cliente, Servicio, Reserva) a implementarlos
    @abstractmethod
    def validar_datos(self):
        pass

    @abstractmethod
    def mostrar_resumen(self):
        pass


# pequena prueba unitaria del modulo 1 (se ejecuta con: python ejercicio1.py pruebas)
def probar_modulo_1():
    print("Probando Modulo 1 (Logs, Excepciones y Clase Abstracta)...")
    GestorLogs.registrar_info("Inicio de pruebas del Modulo 1 por Daniel Zapata.")

    try:
        # forzamos un error de datos invalidos para probar que quede guardado en el archivo .log
        raise DatosInvalidosError("Prueba de error: correo de cliente sin formato valido.")

    except SoftwareFJError as err:
        GestorLogs.registrar_error(err, "Prueba unitaria Modulo 1")
        print("Error capturado y guardado en 'eventos_software_fj.log' correctamente.")

# Modulo 2: GESTION DE CLIENTES

# funcion auxiliar: crea la excepcion, la encadena con su causa original y la registra en el log
def _crear_error(mensaje, contexto, causa=None):
    error = DatosInvalidosError(mensaje)   # creamos la excepcion personalizada con el mensaje
    error.__cause__ = causa                # encadenamiento: guardamos el error original (si existe)
    GestorLogs.registrar_error(error, contexto)  # dejamos constancia en el archivo .log
    return error                           # devolvemos la excepcion para que quien llama haga "raise"


# clase Cliente: hereda de EntidadSistema (el ID de la entidad sera el documento del cliente)
class Cliente(EntidadSistema):

    # patron del nombre: solo letras (con tildes y ñ) y espacios
    _PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$")
    # patron del correo: texto@dominio.extension, sin espacios
    _PATRON_CORREO = re.compile(r"^[\w\.\-+]+@[\w\-]+(\.[\w\-]+)+$")

    # constructor: recibe los datos personales del cliente
    def __init__(self, documento, nombre, correo, telefono):
        documento_ok = Cliente._validar_documento(documento)  # validamos el documento ANTES de crear la entidad
        super().__init__(documento_ok)   # el constructor del padre guarda el ID y la fecha de creacion
        self._nombre = None              # atributo privado del nombre (se llena con el setter)
        self._correo = None              # atributo privado del correo (se llena con el setter)
        self._telefono = None            # atributo privado del telefono (se llena con el setter)
        self._activo = True              # atributo privado: indica si el cliente puede hacer reservas
        self.nombre = nombre             # el setter valida el nombre antes de guardarlo
        self.correo = correo             # el setter valida el correo antes de guardarlo
        self.telefono = telefono         # el setter valida el telefono antes de guardarlo
        GestorLogs.registrar_info(f"Cliente creado correctamente: {self._id_entidad} - {self._nombre}")

    # ---------- VALIDADORES (metodos estaticos reutilizables) ----------

    @staticmethod
    def _validar_documento(documento):
        # si es None o texto vacio, el dato falta
        if documento is None or str(documento).strip() == "":
            raise _crear_error("El documento es obligatorio.", "Validacion documento")
        texto = str(documento).strip()   # convertimos a texto y quitamos espacios sobrantes
        try:
            numero = int(texto)          # intentamos convertir a entero para comprobar que son solo digitos
        except ValueError as causa:      # si falla, capturamos el error original
            # lanzamos nuestra excepcion encadenada con "from" (encadenamiento de excepciones)
            raise _crear_error(f"El documento '{texto}' debe contener solo numeros.",
                               "Validacion documento", causa) from causa
        if numero <= 0 or not texto.isdigit():   # no se permiten negativos, ceros ni signos
            raise _crear_error(f"El documento '{texto}' no es valido.", "Validacion documento")
        if not 5 <= len(texto) <= 12:            # longitud razonable de un documento
            raise _crear_error("El documento debe tener entre 5 y 12 digitos.", "Validacion documento")
        return texto                             # documento correcto

    @staticmethod
    def _validar_nombre(nombre):
        # el nombre debe ser texto (no numero, ni None)
        if not isinstance(nombre, str) or nombre.strip() == "":
            raise _crear_error("El nombre es obligatorio y debe ser texto.", "Validacion nombre")
        limpio = " ".join(nombre.split())        # quitamos espacios repetidos o al inicio/final
        if len(limpio) < 3:                      # minimo 3 caracteres
            raise _crear_error("El nombre debe tener al menos 3 caracteres.", "Validacion nombre")
        if not Cliente._PATRON_NOMBRE.match(limpio):   # solo letras y espacios
            raise _crear_error(f"El nombre '{limpio}' contiene caracteres no permitidos.", "Validacion nombre")
        return limpio.title()                    # lo guardamos con formato "Juan Perez"

    @staticmethod
    def _validar_correo(correo):
        # el correo debe ser texto no vacio
        if not isinstance(correo, str) or correo.strip() == "":
            raise _crear_error("El correo es obligatorio.", "Validacion correo")
        limpio = correo.strip().lower()          # normalizamos a minusculas
        if not Cliente._PATRON_CORREO.match(limpio):   # verificamos el formato con la expresion regular
            raise _crear_error(f"El correo '{limpio}' no tiene un formato valido.", "Validacion correo")
        return limpio

    @staticmethod
    def _validar_telefono(telefono):
        # el telefono es obligatorio
        if telefono is None or str(telefono).strip() == "":
            raise _crear_error("El telefono es obligatorio.", "Validacion telefono")
        limpio = str(telefono).replace(" ", "").replace("-", "")   # quitamos espacios y guiones
        if not limpio.isdigit() or len(limpio) != 10:              # celular colombiano: 10 digitos
            raise _crear_error(f"El telefono '{telefono}' debe tener exactamente 10 digitos numericos.",
                               "Validacion telefono")
        return limpio

    # ENCAPSULACION: PROPERTIES (getters y setters)

    @property
    def documento(self):
        return self._id_entidad          # solo lectura: el documento es el ID y no se puede cambiar

    @property
    def nombre(self):
        return self._nombre              # getter del nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = Cliente._validar_nombre(valor)    # solo asigna si la validacion pasa

    @property
    def correo(self):
        return self._correo              # getter del correo

    @correo.setter
    def correo(self, valor):
        self._correo = Cliente._validar_correo(valor)    # solo asigna si la validacion pasa

    @property
    def telefono(self):
        return self._telefono            # getter del telefono

    @telefono.setter
    def telefono(self, valor):
        self._telefono = Cliente._validar_telefono(valor)  # solo asigna si la validacion pasa

    @property
    def activo(self):
        return self._activo              # getter del estado (solo lectura desde afuera)

    # METODOS DE ESTADO

    def desactivar(self):
        self._activo = False             # un cliente inactivo no deberia poder reservar
        GestorLogs.registrar_info(f"Cliente {self.documento} desactivado.")

    def activar(self):
        self._activo = True              # reactiva al cliente
        GestorLogs.registrar_info(f"Cliente {self.documento} activado.")

    # METODOS ABSTRACTOS DEL PADRE (obligatorio implementarlos)

    def validar_datos(self):
        # vuelve a validar todos los datos del objeto; devuelve True si todo esta bien
        Cliente._validar_documento(self.documento)
        Cliente._validar_nombre(self._nombre)
        Cliente._validar_correo(self._correo)
        Cliente._validar_telefono(self._telefono)
        return True

    def mostrar_resumen(self):
        estado = "Activo" if self._activo else "Inactivo"   # convertimos el booleano en texto
        return (f"Cliente [{self.documento}] {self._nombre} | {self._correo} | "
                f"Tel: {self._telefono} | Estado: {estado}")

    def __str__(self):
        return self.mostrar_resumen()    # al hacer print(cliente) se muestra el resumen

    # REGISTRO SEGURO (try / except / else / finally)

    @classmethod
    def registrar(cls, lista_clientes, documento, nombre, correo, telefono):
        """Crea un cliente y lo agrega a la lista SIN detener el programa si hay error."""
        try:
            nuevo = cls(documento, nombre, correo, telefono)   # puede lanzar DatosInvalidosError
            # evitamos clientes repetidos revisando la lista interna
            if any(c.documento == nuevo.documento for c in lista_clientes):
                raise _crear_error(f"Ya existe un cliente con documento {nuevo.documento}.",
                                   "Registro de cliente")
        except SoftwareFJError as error:    # capturamos cualquier error propio del sistema
            print(f"  [RECHAZADO] {error}")  # avisamos al usuario (el log ya se guardo antes)
            return None                      # devolvemos None: el programa sigue funcionando
        except Exception as error:           # cualquier error inesperado tambien se controla
            GestorLogs.registrar_error(error, "Error inesperado registrando cliente")
            print(f"  [ERROR INESPERADO] {error}")
            return None
        else:
            lista_clientes.append(nuevo)     # solo si NO hubo error, se agrega a la lista
            print(f"  [OK] {nuevo}")
            return nuevo
        finally:
            # el bloque finally se ejecuta SIEMPRE, haya o no error
            GestorLogs.registrar_info("Intento de registro de cliente finalizado.")


# prueba del modulo 2: 5 casos validos e invalidos
def probar_modulo_2():
    print("Probando Modulo 2 (Clientes)...")
    clientes = []   # lista interna donde se guardan los clientes (sin base de datos)

    print("1) Cliente valido:")
    Cliente.registrar(clientes, "1061234567", "jhojhan meneses", "jhojhan@correo.com", "3101234567")
    print("2) Documento con letras (error encadenado):")
    Cliente.registrar(clientes, "10A6B", "Ana Lopez", "ana@correo.com", "3001112233")
    print("3) Correo invalido:")
    Cliente.registrar(clientes, "52123456", "Carlos Ruiz", "carlos.correo.com", "3201112233")
    print("4) Telefono incompleto:")
    Cliente.registrar(clientes, "79456123", "Laura Gomez", "laura@correo.com", "31012")
    print("5) Documento duplicado:")
    Cliente.registrar(clientes, "1061234567", "Otro Nombre", "otro@correo.com", "3101234567")

    print(f"\nClientes registrados correctamente: {len(clientes)}")
    for c in clientes:
        print(" -", c)

# Modulo 3 GESTION DE SERVICIOS Victor Tello
#
# - Servicio (clase abstracta): hereda de la clase abstracta general del sistema (EntidadSistema).
# - ReservaSala, AlquilerEquipo y Asesoria: servicios hijos.
#
# Polimorfismo (cada servicio sobrescribe):
#   - validar_parametros()   -> valida lo que pide cada servicio
#   - calcular_costo_base()  -> formula propia de cada servicio
#   - describir()            -> descripcion propia
#
# Sobrecarga (simulada con parametros opcionales):
#   - calcular_costo(horas, impuesto, descuento, opciones)


# ---------------------------------------------------------------
# Constantes del negocio
# ---------------------------------------------------------------
IVA = 0.19                  # impuesto (fraccion: 0.19 = 19%)
RECARGO_PROYECTOR = 20000   # valor fijo si la sala usa proyector
RECARGO_SEGURO = 0.10       # 10% extra si el equipo lleva seguro
RECARGO_URGENTE = 0.25      # 25% extra si la asesoria es urgente
FACTOR_NIVEL = {"junior": 1.0, "senior": 1.5, "experto": 2.0}


def _error(clase, mensaje, causa=None):
    """Crea el error, lo encadena con su causa (si hay), lo registra en el log y lo devuelve para hacer raise."""
    error = clase(mensaje)
    error.__cause__ = causa      # INTEGRACION: se asigna ANTES de registrar para que el log guarde la causa original
    GestorLogs.registrar_error(error, "Modulo 3 - Servicios")
    return error


# ===============================================================
# CLASE ABSTRACTA: SERVICIO
# ===============================================================
class Servicio(EntidadSistema, ABC):
    """Servicio general que ofrece Software FJ (no se puede instanciar)."""

    def __init__(self, identificador, nombre, tarifa_hora):
        identificador = self._validar_texto(identificador, "El identificador", 20)
        nombre = self._validar_texto(nombre, "El nombre del servicio")
        tarifa_hora = self._validar_tarifa(tarifa_hora)

        super().__init__(identificador)
        self._nombre = nombre
        self._tarifa_hora = tarifa_hora
        self._disponible = True
        GestorLogs.registrar_info(f"Servicio creado: [{identificador}] {nombre}")

    # ---------- encapsulacion: acceso controlado a los datos ----------
    @property
    def nombre(self):
        return self._nombre

    @property
    def tarifa_hora(self):
        return self._tarifa_hora

    @tarifa_hora.setter
    def tarifa_hora(self, nueva_tarifa):
        self._tarifa_hora = self._validar_tarifa(nueva_tarifa)
        GestorLogs.registrar_info(f"Nueva tarifa para '{self._nombre}': ${self._tarifa_hora:,.0f}/hora")

    @property
    def disponible(self):
        return self._disponible

    # ---------- validaciones reutilizables ----------
    @staticmethod
    def _validar_texto(valor, campo, maximo=60):
        if not isinstance(valor, str) or not valor.strip():
            raise _error(DatosInvalidosError, f"{campo} no puede estar vacio.")
        if len(valor.strip()) > maximo:
            raise _error(DatosInvalidosError, f"{campo} no puede superar {maximo} caracteres.")
        return valor.strip()

    @staticmethod
    def _a_numero(valor, campo):
        """Convierte a numero; si falla, encadena la excepcion original."""
        if isinstance(valor, bool):
            raise _error(DatosInvalidosError, f"{campo} debe ser un numero, no un valor logico.")
        try:
            numero = float(valor)
        except (TypeError, ValueError) as error:
            raise _error(DatosInvalidosError, f"{campo} debe ser un numero (recibido: {valor!r}).", error) from error
        if not math.isfinite(numero):
            raise _error(DatosInvalidosError, f"{campo} no es un numero valido.")
        return numero

    @staticmethod
    def _a_entero(valor, campo):
        numero = Servicio._a_numero(valor, campo)
        if numero != int(numero):
            raise _error(DatosInvalidosError, f"{campo} debe ser un numero entero.")
        return int(numero)

    @staticmethod
    def _validar_tarifa(valor):
        tarifa = Servicio._a_numero(valor, "La tarifa")
        if tarifa <= 0:
            raise _error(DatosInvalidosError, "La tarifa por hora debe ser mayor que 0.")
        return tarifa

    @staticmethod
    def _validar_fraccion(valor, campo, incluye_uno):
        """Valida impuesto/descuento expresados como fraccion (0.19 = 19%)."""
        numero = Servicio._a_numero(valor, campo)
        limite_ok = numero <= 1 if incluye_uno else numero < 1
        if numero < 0 or not limite_ok:
            raise _error(DatosInvalidosError, f"{campo} debe ser una fraccion entre 0 y 1 (recibido: {numero:g}).")
        return numero

    def _validar_horas(self, horas, maximo):
        if horas is None:
            raise _error(DatosInvalidosError, "Falta la duracion del servicio (horas).")
        horas = self._a_numero(horas, "La duracion")
        if horas <= 0:
            raise _error(DatosInvalidosError, "La duracion debe ser mayor que 0 horas.")
        if horas > maximo:
            raise _error(DatosInvalidosError,
                         f"'{self._nombre}' no se puede reservar por mas de {maximo} horas (recibido: {horas:g}).")
        return horas

    def _rechazar_opciones_desconocidas(self, opciones, permitidas):
        desconocidas = [clave for clave in opciones if clave not in permitidas]
        if desconocidas:
            raise _error(DatosInvalidosError,
                         f"Opciones no reconocidas para '{self._nombre}': {', '.join(desconocidas)}.")

    # ---------- disponibilidad ----------
    def habilitar(self):
        self._disponible = True
        GestorLogs.registrar_info(f"Servicio habilitado: '{self._nombre}'")

    def deshabilitar(self):
        self._disponible = False
        GestorLogs.registrar_info(f"Servicio deshabilitado: '{self._nombre}'")

    def verificar_disponibilidad(self):
        """Lanza ServicioNoDisponibleError si el servicio no se puede usar."""
        if not self._disponible:
            raise _error(ServicioNoDisponibleError, f"El servicio '{self._nombre}' no esta disponible.")

    # ---------- INTEGRACION: metodos abstractos que exige EntidadSistema (Modulo 1) ----------
    def validar_datos(self):
        # vuelve a validar los datos propios del servicio; True si todo esta bien
        self._validar_texto(self._nombre, "El nombre del servicio")
        self._validar_tarifa(self._tarifa_hora)
        return True

    def mostrar_resumen(self):
        estado = "Disponible" if self._disponible else "No disponible"
        return f"{self.describir()} | Estado: {estado}"

    # ---------- metodos abstractos propios: cada servicio los sobrescribe ----------
    @abstractmethod
    def describir(self):
        """Devuelve una descripcion del servicio."""

    @abstractmethod
    def validar_parametros(self, horas, **opciones):
        """Valida los parametros del servicio y devuelve (horas, opciones) ya limpios."""

    @abstractmethod
    def calcular_costo_base(self, horas, **opciones):
        """Devuelve el costo sin descuento ni impuesto (formula propia de cada servicio)."""

    # ---------- SOBRECARGA (parametros opcionales) ----------
    def calcular_costo(self, horas=None, impuesto=0.0, descuento=0.0, **opciones):
        """
        Calcula el costo total. Python no permite varios metodos con el mismo
        nombre, asi que la sobrecarga se simula con parametros opcionales:

            calcular_costo(2)                     -> costo base
            calcular_costo(2, 0.19)               -> con impuesto
            calcular_costo(2, 0.19, 0.10)         -> con impuesto y descuento
            calcular_costo(2, proyector=True)     -> con opciones propias del servicio

        El descuento se aplica antes que el impuesto.
        """
        try:
            self.verificar_disponibilidad()
            horas, opciones = self.validar_parametros(horas, **opciones)
            impuesto = self._validar_fraccion(impuesto, "El impuesto", incluye_uno=True)
            descuento = self._validar_fraccion(descuento, "El descuento", incluye_uno=False)

            costo = self.calcular_costo_base(horas, **opciones)
            costo = costo * (1 - descuento) * (1 + impuesto)

            if not math.isfinite(costo) or costo <= 0:
                raise _error(CalculoInconsistenteError, f"Calculo inconsistente para '{self._nombre}': costo = {costo}")
        except SoftwareFJError:
            raise       # el error ya fue registrado en el log
        except Exception as error:
            raise _error(CalculoInconsistenteError,
                         f"Error inesperado al calcular el costo de '{self._nombre}'.", error) from error
        else:
            costo = round(costo, 2)
            GestorLogs.registrar_info(f"Costo calculado para '{self._nombre}': ${costo:,.2f}")
            return costo

    def __str__(self):
        return self.describir()


# ===============================================================
# SERVICIO 1: RESERVA DE SALAS
# ===============================================================
class ReservaSala(Servicio):
    """Reserva de salas de reuniones. Opciones: asistentes, proyector."""

    HORAS_MAXIMAS = 12
    OPCIONES = ("asistentes", "proyector")

    def __init__(self, identificador, nombre, tarifa_hora, capacidad):
        capacidad = self._a_entero(capacidad, "La capacidad")
        if not 1 <= capacidad <= 200:
            raise _error(DatosInvalidosError, "La capacidad de la sala debe estar entre 1 y 200 personas.")
        super().__init__(identificador, nombre, tarifa_hora)
        self._capacidad = capacidad

    def describir(self):
        return (f"Sala '{self._nombre}' [{self.id_entidad}] - capacidad: {self._capacidad} personas - "
                f"tarifa: ${self._tarifa_hora:,.0f}/hora")

    def validar_parametros(self, horas, **opciones):
        horas = self._validar_horas(horas, self.HORAS_MAXIMAS)
        self._rechazar_opciones_desconocidas(opciones, self.OPCIONES)

        asistentes = self._a_entero(opciones.get("asistentes", 1), "El numero de asistentes")
        if not 1 <= asistentes <= self._capacidad:
            raise _error(DatosInvalidosError,
                         f"La sala '{self._nombre}' admite maximo {self._capacidad} asistentes "
                         f"(recibido: {asistentes}).")

        proyector = opciones.get("proyector", False)
        if not isinstance(proyector, bool):
            raise _error(DatosInvalidosError, "La opcion 'proyector' debe ser True o False.")

        return horas, {"asistentes": asistentes, "proyector": proyector}

    def calcular_costo_base(self, horas, **opciones):
        costo = self._tarifa_hora * horas
        if opciones.get("proyector", False):
            costo += RECARGO_PROYECTOR
        return costo


# ===============================================================
# SERVICIO 2: ALQUILER DE EQUIPOS
# ===============================================================
class AlquilerEquipo(Servicio):
    """Alquiler de equipos por hora. Opciones: cantidad, seguro."""

    HORAS_MAXIMAS = 72
    OPCIONES = ("cantidad", "seguro")

    def __init__(self, identificador, nombre, tarifa_hora, unidades):
        unidades = self._a_entero(unidades, "Las unidades")
        if unidades < 1:
            raise _error(DatosInvalidosError, "Debe haber al menos 1 unidad del equipo.")
        super().__init__(identificador, nombre, tarifa_hora)
        self._unidades_totales = unidades
        self._unidades_disponibles = unidades

    @property
    def unidades_disponibles(self):
        return self._unidades_disponibles

    def describir(self):
        return (f"Equipo '{self._nombre}' [{self.id_entidad}] - unidades disponibles: "
                f"{self._unidades_disponibles} de {self._unidades_totales} - "
                f"tarifa: ${self._tarifa_hora:,.0f}/hora")

    def verificar_disponibilidad(self):
        super().verificar_disponibilidad()
        if self._unidades_disponibles == 0:
            raise _error(ServicioNoDisponibleError, f"No quedan unidades de '{self._nombre}'.")

    def reservar_unidades(self, cantidad):
        """Descuenta unidades del inventario (lo usa la clase Reserva)."""
        cantidad = self._a_entero(cantidad, "La cantidad")
        if cantidad < 1:
            raise _error(DatosInvalidosError, "La cantidad a reservar debe ser al menos 1.")
        if cantidad > self._unidades_disponibles:
            raise _error(ServicioNoDisponibleError,
                         f"Solo quedan {self._unidades_disponibles} unidad(es) de '{self._nombre}' "
                         f"(solicitadas: {cantidad}).")
        self._unidades_disponibles -= cantidad
        GestorLogs.registrar_info(f"Unidades reservadas de '{self._nombre}': {cantidad}")

    def liberar_unidades(self, cantidad):
        """Devuelve unidades al inventario."""
        cantidad = self._a_entero(cantidad, "La cantidad")
        if cantidad < 1 or self._unidades_disponibles + cantidad > self._unidades_totales:
            raise _error(DatosInvalidosError, "No se pueden liberar esa cantidad de unidades.")
        self._unidades_disponibles += cantidad
        GestorLogs.registrar_info(f"Unidades liberadas de '{self._nombre}': {cantidad}")

    def validar_parametros(self, horas, **opciones):
        horas = self._validar_horas(horas, self.HORAS_MAXIMAS)
        self._rechazar_opciones_desconocidas(opciones, self.OPCIONES)

        cantidad = self._a_entero(opciones.get("cantidad", 1), "La cantidad")
        if cantidad < 1:
            raise _error(DatosInvalidosError, "La cantidad debe ser al menos 1.")
        if cantidad > self._unidades_disponibles:
            raise _error(ServicioNoDisponibleError,
                         f"Solo quedan {self._unidades_disponibles} unidad(es) de '{self._nombre}' "
                         f"(solicitadas: {cantidad}).")

        seguro = opciones.get("seguro", False)
        if not isinstance(seguro, bool):
            raise _error(DatosInvalidosError, "La opcion 'seguro' debe ser True o False.")

        return horas, {"cantidad": cantidad, "seguro": seguro}

    def calcular_costo_base(self, horas, **opciones):
        costo = self._tarifa_hora * horas * opciones.get("cantidad", 1)
        if opciones.get("seguro", False):
            costo = costo * (1 + RECARGO_SEGURO)
        return costo


# ===============================================================
# SERVICIO 3: ASESORIAS ESPECIALIZADAS
# ===============================================================
class Asesoria(Servicio):
    """Asesoria especializada. El nivel del asesor multiplica la tarifa. Opcion: urgente."""

    HORAS_MAXIMAS = 8
    OPCIONES = ("urgente",)

    def __init__(self, identificador, nombre, tarifa_hora, especialidad, nivel="junior"):
        especialidad = self._validar_texto(especialidad, "La especialidad")
        nivel = self._validar_texto(nivel, "El nivel").lower()
        if nivel not in FACTOR_NIVEL:
            raise _error(DatosInvalidosError,
                         f"Nivel no valido: '{nivel}'. Use: {', '.join(FACTOR_NIVEL)}.")
        super().__init__(identificador, nombre, tarifa_hora)
        self._especialidad = especialidad
        self._nivel = nivel

    def describir(self):
        return (f"Asesoria '{self._nombre}' [{self.id_entidad}] - especialidad: {self._especialidad} - "
                f"nivel: {self._nivel} (x{FACTOR_NIVEL[self._nivel]:g}) - "
                f"tarifa base: ${self._tarifa_hora:,.0f}/hora")

    def validar_parametros(self, horas, **opciones):
        horas = self._validar_horas(horas, self.HORAS_MAXIMAS)
        self._rechazar_opciones_desconocidas(opciones, self.OPCIONES)

        urgente = opciones.get("urgente", False)
        if not isinstance(urgente, bool):
            raise _error(DatosInvalidosError, "La opcion 'urgente' debe ser True o False.")

        return horas, {"urgente": urgente}

    def calcular_costo_base(self, horas, **opciones):
        costo = self._tarifa_hora * horas * FACTOR_NIVEL[self._nivel]
        if opciones.get("urgente", False):
            costo = costo * (1 + RECARGO_URGENTE)
        return costo


# prueba del modulo 3 (se ejecuta con: python ejercicio1.py pruebas)
def probar_modulo_3():
    servicios = [
        ReservaSala("S-001", "Sala Ejecutiva", 50000, 10),
        AlquilerEquipo("E-001", "Portatil Dell", 15000, 5),
        Asesoria("A-001", "Ciberseguridad", 80000, "Seguridad informatica", "experto"),
    ]

    print("\n--- POLIMORFISMO: el mismo codigo, resultados distintos ---")
    for servicio in servicios:
        print(servicio.describir())
        print("   2 h, costo base:          ", servicio.calcular_costo(2))
        print("   2 h, con IVA:             ", servicio.calcular_costo(2, IVA))
        print("   2 h, con IVA y 10% dscto: ", servicio.calcular_costo(2, IVA, 0.10))

    print("\n--- OPCIONES PROPIAS DE CADA SERVICIO ---")
    print("Sala con proyector, 8 asistentes:", servicios[0].calcular_costo(2, asistentes=8, proyector=True))
    print("3 equipos con seguro:            ", servicios[1].calcular_costo(2, cantidad=3, seguro=True))
    print("Asesoria urgente:                ", servicios[2].calcular_costo(2, urgente=True))

    print("\n--- ERRORES CONTROLADOS (el programa sigue funcionando) ---")
    intentos = [
        ("Sala con 50 asistentes", lambda: servicios[0].calcular_costo(2, asistentes=50)),
        ("Duracion 'abc'", lambda: servicios[1].calcular_costo("abc")),
        ("Falta la duracion", lambda: servicios[2].calcular_costo()),
        ("Sala con tarifa negativa", lambda: ReservaSala("S-002", "Sala Rota", -5, 10)),
        ("Nivel de asesor inventado", lambda: Asesoria("A-002", "X", 50000, "Redes", "genio")),
    ]
    for descripcion, accion in intentos:
        try:
            accion()
        except SoftwareFJError as error:
            print(f"   {descripcion}: {type(error).__name__} -> {error}")


# MODULO 4: CLASE RESERVA

# clase que une al cliente con el servicio que va a tomar
class Reserva(EntidadSistema):
    def __init__(self, id_reserva, cliente, servicio, duracion):
        super().__init__(id_reserva)
        self._cliente = cliente
        self._servicio = servicio
        self._duracion = duracion
        self._estado = "Pendiente"
        self._costo_final = 0.0
        
        # validamos los datos apenas se intenta crear la reserva
        self.validar_datos()
        GestorLogs.registrar_info(f"Reserva {self.id_entidad} creada en estado Pendiente.")

    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def duracion(self):
        return self._duracion

    @property
    def estado(self):
        return self._estado

    @property
    def costo_final(self):
        return self._costo_final

    # implementacion del metodo abstracto para revisar que todo tenga sentido
    def validar_datos(self):
        if self._cliente is None:
            error = ReservaInvalidaError(f"Reserva {self.id_entidad}: No se asigno ningun cliente valido.")
            GestorLogs.registrar_error(error, "Validacion Reserva")
            raise error

        if self._servicio is None:
            error = ServicioNoDisponibleError(f"Reserva {self.id_entidad}: El servicio solicitado no existe o no esta disponible.")
            GestorLogs.registrar_error(error, "Validacion Reserva")
            raise error

        if not isinstance(self._duracion, (int, float)) or self._duracion <= 0:
            error = CalculoInconsistenteError(f"Reserva {self.id_entidad}: La duracion ({self._duracion}) debe ser mayor a cero.")
            GestorLogs.registrar_error(error, "Validacion Reserva")
            raise error

    # procesa el cobro usando try/except/else/finally y encadenamiento de excepciones
    def procesar_reserva(self, descuento=0.0, impuesto=0.19):
        print(f"-> Procesando calculo de la reserva {self.id_entidad}...")
        try:
            if descuento < 0 or descuento >= 1 or impuesto < 0:
                raise ValueError("Los porcentajes de descuento o impuesto estan fuera de rango.")

            # llamamos el metodo polimorfico del servicio para sacar el costo
            # intenta pasar parametros opcionales y si el servicio recibe solo duracion se adapta
            try:
                costo_calculado = self._servicio.calcular_costo(self._duracion, descuento=descuento, impuesto=impuesto)
            except TypeError:
                costo_base = self._servicio.calcular_costo(self._duracion)
                costo_con_descuento = costo_base * (1 - descuento)
                costo_calculado = costo_con_descuento * (1 + impuesto)

            if costo_calculado <= 0:
                raise ValueError("El resultado del calculo dio un valor negativo o cero.")

        except Exception as e:
            # encadenamiento de excepciones (raise ... from e) exigido en la guia
            error_encadenado = CalculoInconsistenteError(
                f"Fallo al calcular el costo de la reserva {self.id_entidad}."
            )
            error_encadenado.__cause__ = e
            GestorLogs.registrar_error(error_encadenado, "Procesamiento de Reserva")
            raise error_encadenado from e

        else:
            # el bloque else solo corre si no hubo ningun error en el try
            self._costo_final = round(costo_calculado, 2)
            GestorLogs.registrar_info(
                f"Reserva {self.id_entidad} procesada con exito. Total calculado: ${self._costo_final}"
            )
            return self._costo_final

        finally:
            # el bloque finally se ejecuta siempre para dejar constancia del cierre del proceso
            GestorLogs.registrar_info(f"Finalizo el intento de procesamiento para la reserva {self.id_entidad}.")

    # confirma la reserva usando try/except/else
    def confirmar_reserva(self):
        try:
            if self._estado == "Cancelada":
                raise ReservaInvalidaError(f"No se puede confirmar la reserva {self.id_entidad} porque ya fue cancelada.")
            if self._estado == "Confirmada":
                raise ReservaInvalidaError(f"La reserva {self.id_entidad} ya estaba confirmada previamente.")
            if self._costo_final <= 0:
                self.procesar_reserva()

        except SoftwareFJError as err:
            GestorLogs.registrar_error(err, "Confirmar Reserva")
            raise err

        else:
            self._estado = "Confirmada"
            GestorLogs.registrar_info(f"Reserva {self.id_entidad} paso a estado Confirmada.")
            print(f"[OK] Reserva {self.id_entidad} confirmada correctamente.")

    # cancela la reserva usando try/except/finally
    def cancelar_reserva(self, motivo="Solicitud del cliente"):
        try:
            if self._estado == "Cancelada":
                raise ReservaInvalidaError(f"La reserva {self.id_entidad} ya se encuentra cancelada.")
            self._estado = "Cancelada"
            GestorLogs.registrar_info(f"Reserva {self.id_entidad} cancelada. Motivo: {motivo}")
            print(f"[AVISO] Reserva {self.id_entidad} ha sido cancelada ({motivo}).")

        except SoftwareFJError as err:
            GestorLogs.registrar_error(err, "Cancelar Reserva")
            raise err

        finally:
            print(f"-> Estado actual de {self.id_entidad}: {self._estado}")

    def mostrar_resumen(self):
        nombre_cli = getattr(self._cliente, "nombre", self._cliente.id_entidad)
        nombre_srv = getattr(self._servicio, "nombre", self._servicio.id_entidad)
        return (
            f"Reserva [{self.id_entidad}] | Cliente: {nombre_cli} | "
            f"Servicio: {nombre_srv} | Duracion: {self._duracion}h | "
            f"Costo: ${self._costo_final} | Estado: {self._estado}"
        )
