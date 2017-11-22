# BSP support for Cortex-A/R
from support.bsp import BSP
from support.target import DFBBTarget


class CortexARArch(BSP):
    @property
    def name(self):
        return "cortex-ar"

    def __init__(self):
        super(CortexARArch, self).__init__()
        self.add_sources('arch', [
            'src/i-arm_v7ar.ads',
            'src/i-arm_v7ar.adb',
            'src/i-cache.ads',
            'src/i-cache__armv7.adb'])
        self.add_sources('gnarl', [
            'src/s-bbcpsp__arm.ads',
            'src/s-bbcppr__new.ads',
            'src/s-bbcppr__arm.adb',
            'src/s-bbinte__generic.adb'])


class CortexARTarget(DFBBTarget):
    @property
    def target(self):
        return 'arm-eabi'

    @property
    def parent(self):
        return CortexARArch

    @property
    def has_timer_64(self):
        return True

    @property
    def zfp_system_ads(self):
        return 'system-xi-arm.ads'

    def amend_rts(self, rts_profile, conf):
        super(CortexARTarget, self).amend_rts(rts_profile, conf)
        # s-bbcppr.adb uses the r7 register during context switching: this
        # is not compatible with the use of frame pointers that is emited at
        # -O0 by gcc. Let's disable fp even at -O0.
        if 'ravenscar' in rts_profile:
            conf.build_flags['common_flags'] += ['-fomit-frame-pointer']


class Rpi2Base(CortexARTarget):
    @property
    def loaders(self):
        return ('RAM', )

    @property
    def mcu(self):
        return 'cortex-a7'

    @property
    def fpu(self):
        return 'vfpv4'

    @property
    def compiler_switches(self):
        # The required compiler switches
        return ('-mlittle-endian', '-mhard-float',
                '-mcpu=%s' % self.mcu,
                '-mfpu=%s' % self.fpu,
                '-marm', '-mno-unaligned-access')

    @property
    def readme_file(self):
        return 'arm/rpi2/README'

    @property
    def sfp_system_ads(self):
        return 'system-xi-arm-sfp.ads'

    @property
    def full_system_ads(self):
        return 'system-xi-arm-full.ads'

    def __init__(self):
        super(Rpi2Base, self).__init__(
            mem_routines=True,
            small_mem=False)

        self.add_linker_script('arm/rpi2/ram.ld', loader='RAM')
        self.add_sources('crt0', [
            'src/i-raspberry_pi.ads',
            'src/s-macres__rpi2.adb'])
        self.add_sources('gnarl', [
            'src/a-intnam__rpi2.ads',
            'src/s-bbbosu__rpi2.adb'])


class Rpi2(Rpi2Base):
    @property
    def name(self):
        return "rpi2"

    def __init__(self):
        super(Rpi2, self).__init__()

        self.add_sources('crt0', [
            'arm/rpi2/start-ram.S',
            'arm/rpi2/memmap.s',
            'src/s-textio__rpi2-mini.adb'])
        self.add_sources('gnarl', [
            'src/s-bbpara__rpi2.ads'])


class Rpi2Mc(Rpi2Base):
    @property
    def name(self):
        return "rpi2mc"

    def __init__(self):
        super(Rpi2Mc, self).__init__()

        self.add_sources('crt0', [
            'arm/rpi2-mc/start-ram.S',
            'arm/rpi2-mc/memmap.s',
            'src/s-textio__rpi2-pl011.adb'])
        self.add_sources('gnarl', [
            'src/s-bbpara__rpi2.ads'])


class TMS570(CortexARTarget):
    @property
    def name(self):
        if self.variant == 'tms570ls31':
            base = 'tms570'
        else:
            base = 'tms570lc'

        if self.uart_io:
            return "%s_sci" % base
        else:
            return base

    @property
    def loaders(self):
        return ('LORAM', 'FLASH', 'HIRAM', 'LORAM_16M', 'BOOT', 'USER')

    @property
    def cpu(self):
        if self.variant == 'tms570ls31':
            return 'cortex-r4f'
        else:
            return 'cortex-r5'

    @property
    def compiler_switches(self):
        # The required compiler switches
        return ('-mbig-endian', '-mhard-float', '-mcpu=%s' % self.cpu,
                '-mfpu=vfpv3-d16', '-marm')

    @property
    def readme_file(self):
        return 'arm/tms570/README'

    @property
    def system_ads(self):
        return {'zfp': self.zfp_system_ads,
                'ravenscar-sfp': 'system-xi-arm-sfp.ads',
                'ravenscar-esfp': 'system-xi-arm-sfp.ads',
                'ravenscar-full': 'system-xi-arm-full.ads'}

    def amend_rts(self, rts_profile, cfg):
        if rts_profile == 'ravenscar-esfp':
            super(TMS570, self).amend_rts('ravenscar-sfp', cfg)
            cfg.rts_vars['Add_Arith64'] = "yes"

            cfg.rts_vars['Add_Exponent_Int'] = "yes"
            cfg.rts_vars['Add_Exponent_LL_Int'] = "yes"
            cfg.rts_vars['Add_Exponent_LL_Float'] = "yes"

            cfg.rts_vars['Add_Image_Enum'] = "yes"
            cfg.rts_vars['Add_Image_Decimal'] = "yes"
            cfg.rts_vars['Add_Image_LL_Decimal'] = "yes"
            cfg.rts_vars['Add_Image_Float'] = "yes"

            cfg.rts_vars['Add_Math_Lib'] = "hardfloat_sp"

            # cfg.rts_vars['Add_Image_Int'] = "yes"
            # cfg.rts_vars['Add_Image_LL_Int'] = "yes"
        else:
            super(TMS570, self).amend_rts(rts_profile, cfg)

    def __init__(self, variant='tms570ls31', uart_io=False):
        self.variant = variant
        self.uart_io = uart_io
        super(TMS570, self).__init__(
            mem_routines=True,
            small_mem=True)

        self.add_linker_script([
            'arm/tms570/common.ld',
            {'tms570.ld': 'arm/tms570/%s.ld' % self.variant}])
        self.add_linker_script('arm/tms570/flash.ld', loader='FLASH')
        self.add_linker_script('arm/tms570/hiram.ld', loader='HIRAM')
        self.add_linker_script('arm/tms570/loram.ld', loader='LORAM')
        self.add_linker_script('arm/tms570/loram_16m.ld', loader='LORAM_16M')
        self.add_linker_script('arm/tms570/boot.ld', loader='BOOT')
        self.add_linker_switch('-Wl,-z,max-page-size=0x1000',
                               loader=['FLASH', 'HIRAM', 'LORAM',
                                       'LORAM_16M', 'BOOT'])

        self.add_sources('crt0', [
            'arm/tms570/crt0.S',
            'arm/tms570/system_%s.c' % self.variant,
            'arm/tms570/board_init.ads', 'arm/tms570/board_init.adb',
            'src/s-macres__tms570.adb'])
        if self.cpu == 'cortex-r4f':
            self.add_sources('crt0', 'arm/tms570/cortex-r4.S')
        else:
            self.add_sources('crt0', 'arm/tms570/cortex-r5.S')
        if self.uart_io:
            self.add_sources('crt0', 'src/s-textio__tms570-sci.adb')
        else:
            self.add_sources('crt0', 'src/s-textio__tms570.adb')

        self.add_sources('gnarl', [
            'src/a-intnam__tms570.ads',
            'src/s-bbpara__%s.ads' % self.variant,
            'src/s-bbbosu__tms570.adb',
            'src/s-bbsumu__generic.adb'])


class Zynq7000(CortexARTarget):
    @property
    def name(self):
        return "zynq7000"

    @property
    def loaders(self):
        return ('RAM', )

    @property
    def mcu(self):
        return 'cortex-a9'

    @property
    def fpu(self):
        return 'vfpv3'

    @property
    def compiler_switches(self):
        # The required compiler switches
        return ('-mlittle-endian', '-mhard-float',
                '-mcpu=%s' % self.mcu,
                '-mfpu=%s' % self.fpu,
                '-marm', '-mno-unaligned-access')

    @property
    def readme_file(self):
        return 'arm/zynq/README'

    @property
    def sfp_system_ads(self):
        return 'system-xi-arm-gic-sfp.ads'

    @property
    def full_system_ads(self):
        return 'system-xi-arm-gic-full.ads'

    def __init__(self):
        super(Zynq7000, self).__init__(
            mem_routines=True,
            small_mem=False)
        self.add_linker_script('arm/zynq/ram.ld', loader='RAM')
        self.add_sources('crt0', [
            'arm/zynq/start-ram.S',
            'arm/zynq/memmap.inc',
            'src/s-textio__zynq.adb',
            'src/s-macres__zynq.adb'])
        self.add_sources('gnarl', [
            'src/a-intnam__zynq.ads',
            'src/s-bbpara__cortexa9.ads',
            'src/s-bbbosu__cortexa9.adb'])
