# External DEVSJAVA library (local only)

Place the **actual course-provided DEVSJAVA JAR file(s)** here. Do not rename or commit them.
The `.gitignore` in this folder keeps binary dependencies out of the repository.

If the course has not supplied JARs, a **historical DEVS-Suite 2.1.0 JAR** can be tried as
an exploratory compatibility candidate, **not** as proof that it is Dr. Gu's distribution:

https://sourceforge.net/projects/devs-suitesim/files/DEVS-Suite_2.1.0/Executable%20files%20%28Jar%20files%29/DEVS-Suite-2.1.0-20090428.jar/download

SourceForge's download page reports SHA-256:
`e55c3807237822bb8c2f159431e5de93c8623b13de110d7c3d80651b706a9079`.
Verify the downloaded file's hash before use, and don't assume old and new DEVS APIs match.

Then from the repository root run:

```powershell
.\devsjava\scripts\verify-real-devsjava.ps1
```

This is a **compile-only probe**; running the real coordinator is the next milestone.
