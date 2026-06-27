"""Tests for the local VOTable light-curve reader."""

from pathlib import Path

from data_processor.acquisition.xml.votable_light_curve_reader import (
    infer_object_and_filter_from_filename,
    read_votable_light_curve,
)


def test_infer_object_and_filter_from_filename() -> None:
    assert infer_object_and_filter_from_filename("ZTF17aaaacsm_g.xml") == ("ZTF17aaaacsm", "g")


def test_read_votable_light_curve_handles_default_namespace(tmp_path: Path) -> None:
    votable = tmp_path / "ZTF17aaaacsm_g.xml"
    votable.write_text(
        """<?xml version="1.0"?>
<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE>
    <TABLE>
      <FIELD name="oid" datatype="long" />
      <FIELD name="hjd" datatype="double" />
      <FIELD name="mag" datatype="float" />
      <FIELD name="magerr" datatype="float" />
      <FIELD name="catflags" datatype="int" />
      <FIELD name="filtercode" datatype="char" arraysize="*" />
      <DATA>
        <TABLEDATA>
          <TR>
            <TD>123</TD>
            <TD>2459000.5</TD>
            <TD>18.3</TD>
            <TD>0.1</TD>
            <TD>0</TD>
            <TD>zg</TD>
          </TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>
""",
        encoding="utf-8",
    )

    curve = read_votable_light_curve(votable)

    assert curve.object_name == "ZTF17aaaacsm"
    assert curve.file_filter_code == "g"
    assert len(curve.dataframe) == 1
    assert curve.dataframe.loc[0, "hjd"] == 2459000.5
    assert curve.dataframe.loc[0, "filtercode"] == "zg"
