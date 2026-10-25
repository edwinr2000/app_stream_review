MODULE = {
    "id": "gestion",
    "title": "Gestión",
    "description": (
        "Administra pedidos, productos e inventario, clientes y usuarios "
        "desde un mismo módulo."
    ),
    "icon": ":material/inventory_2:",
    "entrypoint": "modules/gestion/views/1_dashboard.py",
    "pages": [
        {
            "path": "modules/gestion/views/1_dashboard.py",
            "title": "Dashboard",
            "icon": ":material/dashboard:",
        },
        {
            "path": "modules/gestion/views/2_pedidos.py",
            "title": "Gestión de pedidos",
            "icon": ":material/shopping_cart:",
        },
        {
            "path": "modules/gestion/views/3_inventario.py",
            "title": "Productos y stock",
            "icon": ":material/inventory:",
        },
        {
            "path": "modules/gestion/views/4_clientes.py",
            "title": "Clientes",
            "icon": ":material/groups:",
        },
        {
            "path": "modules/gestion/views/5_usuarios.py",
            "title": "Usuarios y roles",
            "icon": ":material/admin_panel_settings:",
            "admin_only": True,
        },
    ],
}
