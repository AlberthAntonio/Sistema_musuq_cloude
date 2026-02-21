# app/utils/audio_helper.py

import os
import sys
from pathlib import Path

# Intentar importar librerías de audio
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

class AudioHelper:
    """Manejador de sonidos de alerta con fallback a beeps del sistema"""
    
    def __init__(self):
        # Ruta base del proyecto
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent
        
        self.sounds_path = base_path / "assets" / "sounds"
        self.sounds_path.mkdir(parents=True, exist_ok=True)
        
        # Archivos de sonido
        self.alerta_turno_file = self.sounds_path / "alerta_turno_cruzado.wav"
        self.alerta_error_file = self.sounds_path / "alerta_error.wav"
    
    def reproducir_alerta_turno_cruzado(self):
        """
        3 beeps cortos: bip-bip-bip
        Para turno cruzado (alerta amarilla)
        """
        # Intentar archivo WAV primero
        if self.alerta_turno_file.exists():
            self._reproducir_wav(self.alerta_turno_file)
        else:
            # Fallback: 3 beeps cortos del sistema
            self._beeps_sistema(cantidad=3, duracion=150, frecuencia=1000, pausa=100)
    
    def reproducir_alerta_error(self):
        """
        Beep largo: biiiip
        Para errores (alerta roja)
        """
        # Intentar archivo WAV primero
        if self.alerta_error_file.exists():
            self._reproducir_wav(self.alerta_error_file)
        else:
            # Fallback: 1 beep largo del sistema
            self._beeps_sistema(cantidad=1, duracion=800, frecuencia=800, pausa=0)
    
    def _reproducir_wav(self, archivo):
        """Reproduce un archivo WAV"""
        if AUDIO_ENGINE == "winsound":
            try:
                winsound.PlaySound(
                    str(archivo), 
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )
                return True
            except Exception as e:
                print(f"Error reproduciendo WAV con winsound: {e}")
                return False
        
        elif AUDIO_ENGINE == "pygame":
            try:
                sound = mixer.Sound(str(archivo))
                sound.play()
                return True
            except Exception as e:
                print(f"Error reproduciendo WAV con pygame: {e}")
                return False
        
        return False
    
    def _beeps_sistema(self, cantidad=1, duracion=200, frecuencia=1000, pausa=100):
        """
        Genera beeps usando el sistema
        """
        if AUDIO_ENGINE == "winsound":
            import time
            for i in range(cantidad):
                try:
                    winsound.Beep(frecuencia, duracion)
                    if i < cantidad - 1:  # No pausar después del último
                        time.sleep(pausa / 1000)
                except Exception as e:
                    print(f"Error con winsound.Beep: {e}")
                    # Fallback final: usar MessageBeep
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        
        elif AUDIO_ENGINE == "pygame":
            # Generar beep sintético con pygame
            try:
                import numpy as np
                sample_rate = 22050
                
                for i in range(cantidad):
                    # Generar onda sinusoidal
                    t = np.linspace(0, duracion/1000, int(sample_rate * duracion/1000))
                    wave = np.sin(2 * np.pi * frecuencia * t)
                    
                    # Convertir a formato de audio
                    wave = (wave * 32767).astype(np.int16)
                    stereo_wave = np.column_stack((wave, wave))
                    
                    sound = mixer.Sound(stereo_wave)
                    sound.play()
                    
                    if i < cantidad - 1:
                        import time
                        time.sleep((duracion + pausa) / 1000)
            except Exception as e:
                print(f"Error generando beep con pygame: {e}")
        
        else:
            # Sin motor de audio, imprimir en consola
            beep_text = "BIP " * cantidad
            print(f"🔊 {beep_text.strip()}")
