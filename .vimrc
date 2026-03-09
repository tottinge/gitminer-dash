" gitminer-dash project-local Vim settings

" Use spaces and PEP 8-friendly indentation defaults
set expandtab
set tabstop=4
set shiftwidth=4
set softtabstop=4

" Improve editing quality
set number
" set relativenumber
set hidden
set nowrap
set ignorecase
set smartcase
set incsearch
set hlsearch

" Keep files tidy
set formatoptions-=cro
set textwidth=88
set colorcolumn=89
autocmd BufWritePre * %s/\s\+$//e

" Python-specific defaults
autocmd FileType python setlocal expandtab tabstop=4 shiftwidth=4 softtabstop=4
