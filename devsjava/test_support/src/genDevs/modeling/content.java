package genDevs.modeling;

import GenCol.entity;

/** TEST-ONLY port/value envelope. Not the official DEVSJAVA library. */
public final class content {
    public final String port;
    public final entity value;
    public content(String port, entity value) { this.port = port; this.value = value; }
}
