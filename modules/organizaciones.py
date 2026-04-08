import abc

class IEmpresa(abc.ABC):
    """
    Interface simulation in Python using Abstract Base Classes (ABC).
    Any class inheriting from this interface MUST implement `mostrarEmpresa`.
    """
    
    @abc.abstractmethod
    def mostrarEmpresa(self) -> str:
        """Should return the name and address of the company."""
        pass

class Empresa(IEmpresa):
    """
    Base class representing an Organization.
    Demonstrates protected attributes via the single underscore convention,
    and encapsulates them with getters and setters using the @property decorator.
    """
    def __init__(self, nombre: str, direccion: str):
        # Protected attributes (convention: single underscore)
        self._nombre = nombre
        self._direccion = direccion

    # Getters and Setters for 'nombre'
    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, value):
        if not value:
            raise ValueError("El nombre no puede estar vacío.")
        self._nombre = value

    # Getters and Setters for 'direccion'
    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, value):
        self._direccion = value

    def mostrarEmpresa(self) -> str:
        """
        Implementation of the IEmpresa interface.
        """
        return f"Empresa: {self._nombre} | Dirección: {self._direccion}"

class EmpresaProveedor(Empresa):
    """
    Child class inheriting from Empresa.
    """
    def __init__(self, nombre: str, direccion: str):
        super().__init__(nombre, direccion)

    def mostrarEmpresa(self) -> str:
        """
        Polymorphic override of the interface method.
        """
        return f"Proveedor-> Nombre: {self._nombre} | Dirección: {self._direccion}"

class EmpresaCliente(Empresa):
    """
    Another child class.
    """
    def __init__(self, nombre: str, direccion: str):
        super().__init__(nombre, direccion)

    def mostrarEmpresa(self) -> str:
        return f"Cliente-> Nombre: {self._nombre} | Dirección: {self._direccion}"

def parse_empresa_string(empresa_str: str):
    """
    Helper function to split strings like:
    'Recargas Latinas Fulanito S.A. de C.V., Calle Falsa 1234, Departamento Imaginario, País Raro.'
    into (nombre, direccion) using the first comma as the separator.
    """
    if not isinstance(empresa_str, str) or not empresa_str.strip():
        return "Desconocido", "Desconocido"
        
    if ',' in empresa_str:
        partes = empresa_str.split(',', 1)
        return partes[0].strip(), partes[1].strip()
    
    return empresa_str.strip(), "Dirección no especificada"
