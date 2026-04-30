import pytest
from morselang.symbol_table import SymbolTable, SymbolError


def test_declarar_then_consultar():
    st = SymbolTable()
    st.declarar("X", tipo="NUM", line=1)
    info = st.consultar("X")
    assert info.tipo == "NUM"
    assert info.valor is None
    assert info.linea_declaracion == 1


def test_declarar_twice_raises():
    st = SymbolTable()
    st.declarar("X", tipo="NUM", line=1)
    with pytest.raises(SymbolError):
        st.declarar("X", tipo="NUM", line=2)


def test_asignar_updates_value():
    st = SymbolTable()
    st.declarar("X", tipo="NUM", line=1)
    st.asignar("X", 42)
    assert st.consultar("X").valor == 42


def test_asignar_undeclared_raises():
    st = SymbolTable()
    with pytest.raises(SymbolError):
        st.asignar("Y", 5)


def test_consultar_undeclared_raises():
    st = SymbolTable()
    with pytest.raises(SymbolError):
        st.consultar("Y")


def test_existe_returns_bool():
    st = SymbolTable()
    assert not st.existe("X")
    st.declarar("X", tipo="NUM", line=1)
    assert st.existe("X")


def test_snapshot_returns_dict_for_reporting():
    st = SymbolTable()
    st.declarar("X", tipo="NUM", line=1)
    st.asignar("X", 10)
    snap = st.snapshot()
    assert "X" in snap
    assert snap["X"]["valor"] == 10
