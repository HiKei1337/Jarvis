import ctypes
import threading
import time

VK_VOLUP = 0xAF
VK_VOLDOWN = 0xAE

def _press(vk):
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, 2, 0)

class VolumeSkill:
    @staticmethod
    def _com_init():
        try:
            import comtypes
            comtypes.CoInitialize()
        except Exception:
            pass

    @staticmethod
    def _build():
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            from ctypes import cast, POINTER
            dev = AudioUtilities.GetSpeakers()
            imm = dev
            for attr in ("device", "_device", "imm_device", "mm_device"):
                if hasattr(dev, attr):
                    imm = getattr(dev, attr)
                    break
            interface = imm.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        except Exception:
            pass
        import comtypes
        from comtypes import GUID, IUnknown, COMMETHOD, HRESULT, POINTER
        from ctypes import byref, c_float, c_uint32, c_void_p, cast

        class IMMDevice(IUnknown):
            _iid_ = GUID('{D666063F-1587-4E43-81F1-B948E807363F}')
            _methods_ = [
                COMMETHOD([], HRESULT, 'Activate',
                          (['in'], POINTER(GUID), 'iid'),
                          (['in'], c_uint32, 'dwClsCtx'),
                          (['in'], c_void_p, 'pActivationParams'),
                          (['out'], POINTER(c_void_p), 'ppInterface')),
            ]

        class IMMDeviceEnumerator(IUnknown):
            _iid_ = GUID('{A95664D2-9614-4F35-A746-DE8DB63617E6}')
            _methods_ = [
                COMMETHOD([], HRESULT, 'GetDefaultAudioEndpoint',
                          (['in'], c_uint32, 'dataFlow'),
                          (['in'], c_uint32, 'role'),
                          (['out'], POINTER(IMMDevice), 'ppDevice')),
            ]

        class IAudioEndpointVolume(IUnknown):
            _iid_ = GUID('{5CDF2C82-841E-4546-9722-0CF74078229A}')
            _methods_ = [
                COMMETHOD([], HRESULT, 'RegisterControlChangeNotify', (['in'], c_void_p, 'p')),
                COMMETHOD([], HRESULT, 'UnregisterControlChangeNotify', (['in'], c_void_p, 'p')),
                COMMETHOD([], HRESULT, 'GetChannelCount', (['out'], POINTER(c_uint32), 'c')),
                COMMETHOD([], HRESULT, 'SetMasterVolumeLevel',
                          (['in'], c_float, 'l'), (['in'], c_void_p, 'g')),
                COMMETHOD([], HRESULT, 'SetMasterVolumeLevelScalar',
                          (['in'], c_float, 'l'), (['in'], c_void_p, 'g')),
            ]

        enum = comtypes.CoCreateInstance(
            GUID('{BCDE0395-E52F-467C-8E3D-C4579291692E}'), IMMDeviceEnumerator)
        dev = enum.GetDefaultAudioEndpoint(0, 1)
        ptr = dev.Activate(byref(IAudioEndpointVolume._iid_), 23, None)
        return cast(ptr, POINTER(IAudioEndpointVolume))

    @staticmethod
    def _by_keys(pct):
        for _ in range(50):
            _press(VK_VOLDOWN)
            time.sleep(0.02)
        for _ in range(int(round(pct / 2))):
            _press(VK_VOLUP)
            time.sleep(0.02)

    def set_level(self, value):
        try:
            v = float(value)
        except (TypeError, ValueError):
            return "не понял громкость"
        pct = v * 10 if v <= 10 else v
        pct = max(0.0, min(100.0, pct))
        out = {}

        def work():
            self._com_init()
            try:
                vol = self._build()
                vol.SetMasterVolumeLevelScalar(pct / 100.0, None)
                out["ok"] = f"громкость {pct:.0f}%"
            except Exception as e:
                out["err"] = str(e)

        t = threading.Thread(target=work)
        t.start()
        t.join(5)
        if out.get("ok"):
            return out["ok"]
        self._by_keys(pct)
        return f"громкость ~{pct:.0f}% (медиа-клавишами)"
