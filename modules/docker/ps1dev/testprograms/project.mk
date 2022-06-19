include ../../Makefile.cfg

all: $(PROJNAME)_extra
	mkdir -p ~/.build-out/cd_root
	$(EXAMPLES_CC) $(EXAMPLES_CFLAGS) -DEXAMPLES_VMODE=$(EXAMPLES_VMODE) -o ~/.build-out/$(PROJNAME).elf $(PROJNAME).c \
		$(EXAMPLES_LIBS) $(PROJ_LIBS) $(EXAMPLES_LDFLAGS)
	cd ~/.build-out; 
	cd ~/.build-out; pwd
	cd ~/.build-out; find .
	cd ~/.build-out; elf2exe $(PROJNAME).elf $(PROJNAME).exe
	cd ~/.build-out; cp $(PROJNAME).exe cd_root/
	cd ~/.build-out; systemcnf $(PROJNAME).exe > cd_root/system.cnf
	cd ~/.build-out; $(MKISOFS_COMMAND) -o $(PROJNAME).hsf -V $(PROJNAME) -sysid PLAYSTATION cd_root
	cd ~/.build-out; mkpsxiso $(PROJNAME).hsf $(PROJNAME).bin $(CDLIC_FILE)
	cd ~/.build-out; find .
	rm -f $(PROJNAME).hsf

clean: $(PROJNAME)_clean_extra
	rm -f ~/.build-out/$(PROJNAME).bin ~/.build-out/$(PROJNAME).cue ~/.build-out/$(PROJNAME).exe ~/.build-out/$(PROJNAME).elf
	rm -fr ~/.build-out/cd_root
