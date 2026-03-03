import argparse
from pathlib import Path
from PIL import Image
import sys


def convertir_a_webp(path_in: Path, path_out: Path, quality: int = 80, overwrite: bool = False):
    if path_out.exists() and not overwrite:
        return False, f"skipped (exists): {path_out.name}"
    try:
        img = Image.open(path_in)
        if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        path_out.parent.mkdir(parents=True, exist_ok=True)
        img.save(path_out, format="WEBP", quality=quality, lossless=False)
        return True, f"converted: {path_in.name} → {path_out.name}"
    except Exception as e:
        return False, f"error {path_in.name}: {e}"


def find_images(directory: Path, exts, recursive: bool):
    if recursive:
        iterator = directory.rglob("*")
    else:
        iterator = directory.glob("*")
    for p in iterator:
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def main():
    base = Path(__file__).resolve().parent
    # Si quieres forzar un nombre de carpeta de salida al mismo nivel del script,
    # escribe el nombre aquí (p.ej. "webp_out"). Si queda en None, usa la CLI.
    SCRIPT_OUTPUT_FOLDER_NAME = "Equipos_Escaleras"

    parser = argparse.ArgumentParser(description="Convertir imágenes a WEBP en lote")
    parser.add_argument("--input-dir", "-i", default=str(base), help="Carpeta con las imágenes (por defecto: carpeta del script)")
    parser.add_argument("--output-dir", "-o", default=None, help="Carpeta de salida (por defecto: misma carpeta de entrada)")
    parser.add_argument("--new-folder", "-n", default=None, help="Nombre de subcarpeta dentro de la carpeta de salida/entrada para guardar los .webp")
    parser.add_argument("--script-folder", "-s", default=None, help="Nombre de carpeta a crear al nivel del script (ignora -o/-i when set)")
    parser.add_argument("--flatten", action="store_true", help="Guardar todos los .webp en la misma carpeta (sin subcarpetas)")
    parser.add_argument("--quality", "-q", type=int, default=80, help="Calidad WEBP 0-100 (por defecto 80)")
    parser.add_argument("--exts", default=".png,.jpg,.jpeg,.tiff,.bmp,.gif", help="Extensiones a procesar separadas por comas")
    parser.add_argument("--recursive", "-r", action="store_true", help="Buscar recursivamente")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescribir archivos webp existentes")
    parser.add_argument("--delete-original", action="store_true", help="Eliminar archivos originales después de convertir")

    args = parser.parse_args()
    input_dir = Path(args.input_dir).expanduser().resolve()
    if SCRIPT_OUTPUT_FOLDER_NAME:
        output_dir = (base / SCRIPT_OUTPUT_FOLDER_NAME).resolve()
    elif args.script_folder:
        output_dir = (base / args.script_folder).resolve()
    else:
        if args.output_dir:
            base_output = Path(args.output_dir).expanduser().resolve()
        else:
            base_output = input_dir
        if args.new_folder:
            output_dir = (base_output / args.new_folder).resolve()
        else:
            output_dir = base_output
    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.exts.split(",")}

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input dir no existe: {input_dir}")
        sys.exit(1)

    files = list(find_images(input_dir, exts, args.recursive))
    if not files:
        print("No se encontraron imágenes con las extensiones especificadas.")
        return

    total = len(files)
    ok = 0
    fail = 0
    skipped = 0

    for p in files:
        if args.flatten:
            out_path = output_dir / p.with_suffix(".webp").name
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            rel = p.relative_to(input_dir)
            out_path = output_dir / rel.with_suffix(".webp")
            out_path.parent.mkdir(parents=True, exist_ok=True)
        success, msg = convertir_a_webp(p, out_path, quality=args.quality, overwrite=args.overwrite)
        if success:
            ok += 1
            print(f"✔ {msg}")
            if args.delete_original:
                try:
                    p.unlink()
                except Exception as e:
                    print(f"warning: no pudo borrar {p.name}: {e}")
        else:
            if msg.startswith("skipped"):
                skipped += 1
                print(f"- {msg}")
            else:
                fail += 1
                print(f"✖ {msg}")

    print(f"\nResumen: total={total}, convertidas={ok}, fallidas={fail}, omitidas={skipped}")


if __name__ == "__main__":
    main()
