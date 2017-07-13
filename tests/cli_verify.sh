export CFG_DIR="/tmp/test_b2p_compl"
_mdvl="$CFG_DIR/modules/mdvl"
test -e "$_mdvl/mdvl.py" || {
    /bin/rm -rf "$_mdvl"
    mkdir -p "$_mdvl"
    echo 'fetching markdown renderer mdvl'
    curl "https://raw.githubusercontent.com/axiros/mdvl/master/mdvl.py" 1>"$_mdvl/mdvl.py"
}


comp_func=
comp_height=5
rlt_compgen () {
    export ubc_line="$COMP_LINE"
    export ubc_d_cfg="$CFG_DIR"
    #export ubc_match_substr="y"
    export ubc_term_width="$COLUMNS"
    # we get back function name and height
    #res=( `python -Ss "../completer.py"` )
    python -Ss "../completer.py" # yes you can get a tracepoint in foreground


    echo -e "\n\n\n=====================" >> /tmp/reslog
    for line in ${res[@]}; do echo $line>>/tmp/reslog; done

    echo -e "=====================" >> /tmp/reslog
    _new_comp_func="${res[0]}"
    _new_comp_height="${res[1]}"
    _new_cols="$COLUMNS"
    if [ "x$_new_cols" != "x$cols" ]; then comp_func=; fi
    cols="$COLUMNS"

    read -ra COMPREPLY <<< ${res[@]:2}
}

# nosort is bash > 4.4 (not sorting complete options):
complete -o nosort -F rlt_compgen mm




archive() {
    return


    #echo "$COMP_WORDBREAKS" >> /tmp/wb
    #local cur=${COMP_WORDS[$COMP_CWORD]}
    #local last="$3"
    #echo "$last" > /tmp/last
    #local pos="$COMP_POINT"
    #export ubc_cmd="${COMP_WORDS[0]}"


    echo "new:$_new_comp_height:$_new_comp_func-old:$comp_height:$comp_func" >> /tmp/foo1

    #if [ "$_new_comp_height" -lt "$comp_height" ]; then { comp_func=; comp_height=5; return; }; fi

    if [[ "x$_new_comp_func" == "x$comp_func" ]]; then
        echo -e "\033[${comp_height}A"
        for ((i=1;i<=$comp_height;i++)); do echo -e "\033[K"; done
        echo -e "\033[${comp_height}A"
    fi
    comp_func="$_new_comp_func"
    comp_height="$_new_comp_height"
}

