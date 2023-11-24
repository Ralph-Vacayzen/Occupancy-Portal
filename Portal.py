import streamlit as st
import pandas as pd
import functions

from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title='Occupancy Portal', page_icon='🗓️', layout="centered", initial_sidebar_state="auto", menu_items=None)



read = st.connection("gsheets", type=GSheetsConnection)
keys = read.read(spreadsheet=st.secrets['ppr'],worksheet='PARTNERS',  ttl='10m').dropna()
sets = read.read(spreadsheet=st.secrets['ppr'],worksheet='BEACH',     ttl='10m')
occ  = read.read(spreadsheet=st.secrets['ppr'],worksheet='OCCUPANCY', ttl='10m')

write = st.connection("gsheets", type=GSheetsConnection)


st.caption('VACAYZEN')
st.title('Occupancy Portal')


if 'key'           not in st.session_state: st.session_state['key']           = ''
if 'list'          not in st.session_state: st.session_state['list']          = []
if 'button_login'  not in st.session_state: st.session_state['button_login']  = False
if 'button_submit' not in st.session_state: st.session_state['button_submit'] = False

if not st.session_state['button_login']:
    st.info('Welcome! This is the place to submit new occupancy or view submitted occupancy to Vacayzen.')
    st.session_state['key'] = st.text_input('Please provide your partnernship passkey:')

    if st.button('Login', use_container_width=True):

        if not st.session_state['key'] in keys.PASSKEY.values:
            st.toast('Not a valid passkey.')
            st.session_state['button_login'] = False

        else:
            st.session_state['button_login'] = True
            st.rerun()
    

if st.session_state['button_login']:
    partner      = keys[keys.PASSKEY == st.session_state['key']]['PARTNER'].values[0]
    parnter_name = functions.remove_VRBO_from_partner_name(partner)
    units        = sets[sets.PARTNER == partner]['UNIT CODE'].unique()

    isAbleToSubmit   = False
    if len(units) > 0: isAbleToSubmit = True


    st.subheader('Hello, ' + parnter_name + '!')
    st.write('What would you like to do?')
    tab_submit, tab_submitted = st.tabs(['Submit new occupancy','View submitted occupancy'])

    with tab_submit:
        if not isAbleToSubmit:
            target_email = functions.get_target_email_from_partner_situations(partner, sets)

            st.warning('It appears that we do not have any active seasonal beach service units for you.')
            'Please communicate any questions or concerns to: ' + target_email
        
        else:

            tab_manual, tab_upload = st.tabs(['One-by-one','Upload in bulk'])

            with tab_manual:
                l, m, r = st.columns(3)
                list = st.session_state['list']

                unit      = l.selectbox('Unit',units)
                arrival   = m.date_input('Arrival')
                departure = r.date_input('Departure')

                l, r = st.columns(2)

                if l.button('Add to list', use_container_width=True):
                    list.append([unit, arrival, departure])
                
                if r.button('Remove last entry from list', use_container_width=True):
                    list = list[:-1]
                
                st.session_state['list'] = list
                if (len(list) > 0):
                    df = pd.DataFrame(st.session_state['list'], columns=['Unit','Arrival','Departure'])
                    st.dataframe(df,use_container_width=True,hide_index=True)

                    if st.button('Submit', use_container_width=True, type='primary', key='submit_onebyone'):
                        df = pd.DataFrame(list,columns=['Unit','Arrival','Departure'])
                        df['Partner']       = partner
                        df['Type']          = 'Portal'
                        df['Date Received'] = pd.to_datetime('now')
                        df = df[['Partner','Unit','Arrival','Departure','Type','Date Received']]

                        st.toast('Submitting...')

                        tab = partner + ' | ' + str(pd.to_datetime('now'))[:19]
                        write.create(worksheet=tab,data=df)
                        list = []
                        st.session_state['list'] = list
                        st.rerun()
                        
                
            
            with tab_upload:
                temp = pd.DataFrame([], columns=['Unit','Arrival','Departure'])
                temp.Unit = units
                st.info('You must submit for active beach service program units.')
                st.info('You must provide DD/MM/YY or DD/MM/YYYY format, for arrival and departure date fields.')
                st.success('The below template includes each of your active beach service units pre-populated.')
                st.download_button(
                    'Download template',
                    temp.to_csv(index=False).encode(),
                    'occupancy_template.csv',
                    use_container_width=True,
                    help='The template includes your unit IDs pre-populated.',
                    key='template'
                    )
                
                if "file_uploader_key" not in st.session_state:
                    st.session_state["file_uploader_key"] = 0
                
                file = st.file_uploader('Please provide your occupancy submission here:','CSV',key=st.session_state["file_uploader_key"])
                
                if file is not None:
                    df = pd.read_csv(file)

                    def is_unit_valid(row):   return row.Unit in units
                    def has_valid_dates(row): return isinstance(row.Arrival, pd.Timestamp) and isinstance(row.Departure, pd.Timestamp)
                    
                    df['Arrival'] = pd.to_datetime(df['Arrival']).dt.normalize()
                    df['Departure'] = pd.to_datetime(df['Departure']).dt.normalize()
                    df['Active Unit?'] = df.apply(is_unit_valid, axis=1)
                    df['Valid Dates?'] = df.apply(has_valid_dates, axis=1)

                    with st.expander('**Submission Validation**'):
                        errors = False
                        st.dataframe(df,use_container_width=True,hide_index=True)

                        if False in df['Active Unit?'].values:
                            errors = True
                            st.warning('Submissions for non-active beach service program units will not be recorded.')
                        if False in df['Valid Dates?'].values:
                            errors = True
                            st.warning('Submissions for non-valid arrival and departure dates will not be recorded.')

                        if errors:
                            err = df
                            err = err[(~err['Active Unit?'] | ~err['Valid Dates?'])]
                            err = err[['Unit','Arrival','Departure']]


                            st.download_button(
                                'Download rows that did not pass validation',
                                err.to_csv(index=False).encode(),
                                'occupancy_validation.csv',
                                use_container_width=True,
                                help='The download will only include rows that did not pass the validation checks.',
                                key='errors'
                                )

                    df = df[df['Active Unit?']]
                    df = df[df['Valid Dates?']]

                    if not len(df) > 0:
                        st.error('Your submitted file did not contain any valid rows to submit.')
                        st.info('Please see the **Submission Validation** dropdown section above for more detail.')
                    else:
                        '**Submission Preview**'
                        df = df[['Unit','Arrival','Departure']]
                        st.dataframe(df,use_container_width=True,hide_index=True)

                        if st.button('Submit', use_container_width=True, type='primary', key='submit_upload'):
                            df['Partner']       = partner
                            df['Type']          = 'Portal'
                            df['Date Received'] = pd.to_datetime('now')
                            df                  = df[['Partner','Unit','Arrival','Departure','Type','Date Received']]

                            st.toast('Submitting...')

                            tab = partner + ' | ' + str(pd.to_datetime('now'))[:19]
                            write.create(worksheet=tab,data=df)

                            st.session_state["file_uploader_key"] += 1
                            st.rerun()

                

    with tab_submitted:

        df = occ[occ.PARTNER == partner]
        df = df[['PROPERTY CODE','ARRIVAL','DEPARTURE']]
        df.columns = ['Unit','Arrival','Departure']

        if (len(df) == 0):
            st.warning('It appears that we do not have any occupancy data from you.')

        else:
            st.dataframe(df, hide_index=True, use_container_width=True)
        
        target_email = functions.get_target_email_from_partner_situations(partner, sets)
        st.info('If you have submitted occupancy, and you do not see your submission here, it is still under review.')
        'Please communicate any questions or concerns to: ' + target_email