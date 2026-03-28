# app/utils/audio_helper.py

import sys
import math
import struct
import tempfile
import os
from pathlib import Path

# Intentar importar winsound (Windows) o pygame como fallback
try:
    import winsound
    AUDIO_ENGINE = "winsound"
except ImportError:
    try:
        from pygame import mixer
        mixer.init()
        AUDIO_ENGINE = "pygame"
    except ImportError:
        AUDIO_ENGINE = None


def _generar_wav(patrones: list, sample_rate: int = 44100) -> bytes:
    """
    Genera bytes de un archivo WAV PCM en memoria.

    patrones: lista de tuplas (frecuencia_hz, duracion_ms)
              frecuencia=0 → silencio (pausa)
    """
    muestras = []
    for frecuencia, duracion_ms in patrones:
        n_muestras = int(sample_rate * duracion_ms / 1000)
        if frecuencia == 0:
            muestras.extend([0] * n_muestras)
        else:
            fade = max(1, int(sample_rate * 0.005))  # 5ms fade in/out para evitar clic
            for i in range(n_muestras):
                amp = 32767
                if i < fade:
                    amp = int(32767 * i / fade)
                elif i > n_muestras - fade:
                    amp = int(32767 * (n_muestras - i) / fade)
                val = int(amp * math.sin(2 * math.pi * frecuencia * i / sample_rate))
                muestras.append(max(-32768, min(32767, val)))

    data = struct.pack(f"<{len(muestras)}h", *muestras)

    nc  = 1
    bps = 16
    br  = sample_rate * nc * bps // 8
    ba  = nc * bps // 8

    hdr = (
        b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVE"
        + b"fmt " + struct.pack("<IHHIIHH", 16, 1, nc, sample_rate, br, ba, bps)
        + b"data" + struct.pack("<I", len(data))
    )
    return hdr + data


def _guardar_temp(wav_bytes: bytes, sufijo: str) -> str:
    """Guarda bytes WAV en un archivo temporal y devuelve su ruta."""
    fd, path = tempfile.mkstemp(suffix=f"_{sufijo}.wav", prefix="musuq_")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(wav_bytes)
    return path


class AudioHelper:
    """
    Reproduce sonidos usando archivos WAV temporales generados en memoria.
    Usa SND_FILENAME | SND_ASYNC → verdaderamente asíncrono, no bloquea la UI
    y funciona aunque grab_set() esté activo en un modal.
    Los archivos temporales se crean una sola vez al instanciar la clase.
    """

    def __init__(self):
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent

        self.sounds_path = base_path / "assets" / "sounds"
        self.sounds_path.mkdir(parents=True, exist_ok=True)

        # Archivos WAV externos opcionales (si existen, se usan en lugar de los generados)
        self.alerta_turno_file = self.sounds_path / "alerta_turno_cruzado.wav"
        self.alerta_error_file = self.sounds_path / "alerta_error.wav"

        # Generar y guardar los WAVs sintéticos como archivos temporales
        self._tmp_exito        = _guardar_temp(_generar_wav([(1200, 120)]),                                "exito")
        self._tmp_turno_cruzado = _guardar_temp(_generar_wav([(900, 220),(0,80),(900,220),(0,80),(900,220)]), "turno_cruzado")
        self._tmp_error        = _guardar_temp(_generar_wav([(380, 600)]),                                "error")

        print(f"[Audio] Archivos temp generados: {self._tmp_exito}")

    # ─────────────────────── API pública ───────────────────────────────

    def reproducir_registro_exitoso(self):
        """1 pip corto agudo — confirmación de registro exitoso."""
        self._play_path(self._tmp_exito)

    def reproducir_alerta_turno_cruzado(self):
        """3 beeps medianos — alerta de turno cruzado."""
        path = str(self.alerta_turno_file) if self.alerta_turno_file.exists() else self._tmp_turno_cruzado
        self._play_path(path)

    def reproducir_alerta_error(self):
        """1 tono grave largo — error."""
        path = str(self.alerta_error_file) if self.alerta_error_file.exists() else self._tmp_error
        self._play_path(path)

    # ─────────────────────── Internos ──────────────────────────────────

    def _play_path(self, path: str):
        """
        Reproduce un archivo WAV de forma asíncrona.
        SND_FILENAME | SND_ASYNC es la combinación más estable en Windows.
        """
        if AUDIO_ENGINE == "winsound":
            try:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                print(f"[Audio] ✅ Reproduciendo: {os.path.basename(path)}")
            except Exception as e:
                print(f"[Audio] Error PlaySound: {e}")
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass

        elif AUDIO_ENGINE == "pygame":
            try:
                sound = mixer.Sound(path)
                sound.play()
            except Exception as e:
                print(f"[Audio] Error pygame: {e}")

        else:
            print("[Audio] 🔊 BIP (sin motor de audio)")

