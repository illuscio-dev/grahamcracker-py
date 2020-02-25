from dataclasses import dataclass, field

from grahamcracker import schema_for, DataSchemaConcrete, dataclass_schema


class TestClassDocstring:
    def test_regular(self):
        @dataclass
        class X:
            key: str

        @schema_for(X)
        class XSchema(DataSchemaConcrete):
            """Docstring Stuff"""

            pass

        assert XSchema.__doc__ == "Docstring Stuff"

    def test_from_class_regular(self):
        @dataclass
        class X:
            """Docstring Stuff"""

            key: str

        @schema_for(X)
        class XSchema(DataSchemaConcrete):
            pass

        assert XSchema.__doc__ == "Docstring Stuff"

    def test_schema_priority(self):
        @dataclass
        class X:
            """Docstring Data"""

            key: str

        @schema_for(X)
        class XSchema(DataSchemaConcrete):
            """Docstring Schema"""

        assert XSchema.__doc__ == "Docstring Schema"


class TestAttrDocstringDescriptions:
    def test_single(self):
        @dataclass
        class XTestSingle:
            key: str
            """key description"""

        schema = dataclass_schema(XTestSingle)

        mfields = schema._declared_fields
        assert mfields["key"].metadata["description"] == "Key description."

    def test_single_newlined(self):
        @dataclass
        class XTestNewlined:
            key: str
            """
            key description
            """

        schema = dataclass_schema(XTestNewlined)

        mfields = schema._declared_fields
        assert mfields["key"].metadata["description"] == "Key description."

    def test_single_multiline(self):
        @dataclass
        class XTestMultiline:
            key: str
            """
            This is a really long description that may go into a multiline thing. blah
            blah blah
            """

        schema = dataclass_schema(XTestMultiline)

        mfields = schema._declared_fields
        assert mfields["key"].metadata["description"] == (
            "This is a really long description that may go into a multiline thing. blah"
            "\nblah blah."
        )

    def test_double(self):
        @dataclass
        class XTestDouble:
            key: str
            """key description"""

            key2: int
            """a number"""

        schema = dataclass_schema(XTestDouble)

        mfields = schema._declared_fields
        assert mfields["key"].metadata["description"] == "Key description."
        assert mfields["key2"].metadata["description"] == "A number."

    def test_inheritance(self):
        @dataclass
        class XInheritBase:
            key3: str
            """key description"""

        @dataclass
        class XInheritSubclass(XInheritBase):
            key4: int
            """a number"""

        schema = dataclass_schema(XInheritSubclass)

        mfields = schema._declared_fields
        assert mfields["key3"].metadata["description"] == "Key description."
        assert mfields["key4"].metadata["description"] == "A number."

    def test_inheritance_override(self):
        @dataclass
        class XInheritOverrideBase:
            key7: str
            """key description"""

        @dataclass
        class XInheritOverrideSubclass(XInheritOverrideBase):
            key7: str
            """key description new"""

            key8: int
            """a number"""

        schema = dataclass_schema(XInheritOverrideSubclass)

        mfields = schema._declared_fields
        assert mfields["key7"].metadata["description"] == "Key description new."
        assert mfields["key8"].metadata["description"] == "A number."

    def test_missing_description(self):
        @dataclass
        class XMissingDescription:
            key5: str
            key6: int
            """a number"""

        schema = dataclass_schema(XMissingDescription)

        mfields = schema._declared_fields
        assert "description" not in mfields["key5"].metadata
        assert mfields["key6"].metadata["description"] == "A number."

    def test_wacky(self):
        @dataclass
        class XWacky:
            """Dpcstring here"""

            key_a: str
            """key_a description"""

            key_b: int = 10

            def a_method(self):
                """it's own docstring"""
                pass

            key_c: float = 1.0
            """key_c description"""

            @property
            def a_prop(self) -> None:
                """a prop description"""
                return

            key_d: dict = field(default_factory=dict)
            """key_d description"""

        schema = dataclass_schema(XWacky)

        mfields = schema._declared_fields
        assert mfields["key_a"].metadata["description"] == "Key_a description."
        assert mfields["key_c"].metadata["description"] == "Key_c description."
        assert mfields["key_d"].metadata["description"] == "Key_d description."
        assert "description" not in mfields["key_b"].metadata

    def test_codegen(self):
        @dataclass
        class XDeclared:
            key21: str
            """key21 description"""

        genned = type("XCodeGen", (XDeclared,), dict())

        schema = dataclass_schema(genned)
        mfields = schema._declared_fields

        assert mfields["key21"].metadata["description"] == "Key21 description."
