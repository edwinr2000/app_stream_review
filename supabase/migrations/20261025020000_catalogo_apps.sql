create table if not exists public.app_catalog (
    id text primary key,
    title text not null,
    description text not null,
    icon text not null,
    enabled boolean not null default true,
    created_at timestamptz not null default now()
);

alter table public.app_catalog enable row level security;

insert into public.app_catalog (id, title, description, icon)
values
    (
        'gestion',
        'Gestión',
        'Administra pedidos, productos e inventario, clientes y usuarios desde un mismo módulo.',
        ':material/inventory_2:'
    ),
    (
        'reloj_pdf',
        'Reloj PDF',
        'Genera un PDF descargable con la fecha y hora actuales.',
        ':material/schedule:'
    ),
    (
        'qr_generator',
        'QR Generator',
        'Crea códigos QR de enlaces, texto o redes Wi-Fi.',
        ':material/qr_code_2:'
    ),
    (
        'json_formatter',
        'JSON Formatter',
        'Valida, formatea y minifica documentos JSON.',
        ':material/data_object:'
    ),
    (
        'pdf_toolbox',
        'PDF Toolbox',
        'Une, divide y convierte documentos PDF y Word.',
        ':material/picture_as_pdf:'
    )
on conflict (id) do update set
    title = excluded.title,
    description = excluded.description,
    icon = excluded.icon;
