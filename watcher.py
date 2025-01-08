print('watcher start')
try:
    from main import main
    main()
except Exception:
    print('CRASH!')