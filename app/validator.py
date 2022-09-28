from array import array
import json
import os
import yaml
import traceback

from .cache import Cache

class Validator: 

    def __init__(self, cache: Cache):
        self.cache = cache   

    def load_yaml(self, file):
        parsed_yaml = {}
        with open(file, "r") as stream:
            try:
                parsed_yaml=yaml.safe_load(stream)
            except yaml.YAMLError as ex:
                print(ex)
        return parsed_yaml

    async def load(self):
        cwd = os.getcwd() 
        data = self.load_yaml(f'{cwd}/app/validators/data.yaml')
        await self.cache.db.validators.delete_many({})
        await self.cache.db.validators.insert_many(data)
        count = await self.cache.db.validators.count_documents({})
        print(f"Validators loaded: {count}")

    async def get(self, name: str) -> dict:
        """
            Get Validator by name
        """
        return await self.cache.sync("VALIDATOR", "validators", "name", name, 1)

    async def validate(self, evt):
        errors = []
        event_type = evt['type']
        print(f"Validating event {event_type}...")
        vals = await self.cache.sync("VALIDATOR", "validators", "name", event_type, 1)
        if not vals:
            return errors
        else:
            for atr in vals['attributes']:                
                meta = evt['meta']
                name = atr['name']
                if not meta:
                    continue              
                # fill the evt status
                if 'status' in atr:
                    evt['status'] = atr['status']  
                # if the attribute is mandatory, check if it is in the meta block
                if atr['mandatory']:                    
                    if name in meta:
                        print (f"{name}: OK")
                    else:
                        print (f"{name}: NOT_FOUND")
                        errors.append(f"{name}: NOT_FOUND")
                        continue
                # validate str attribute type
                if isinstance(atr['type'], str) and  (atr['type'] == 'str'):
                    if name not in meta:
                        continue
                    if isinstance(meta[name], str):
                        print (f"{name}: IS_STR")
                    else:
                        print (f"{name}: NOT_STR")
                        errors.append(f"{name}: NOT_STR")
                        continue
                # validate int attribute type
                if isinstance(atr['type'], str) and (atr['type'] == 'int'):
                    if name not in meta:
                        continue
                    if isinstance(meta[name], int):
                        print (f"{name}: IS_INT")
                    else:
                        print (f"{name}: NOT_INT")
                        errors.append(f"{name}: NOT_INT")
                        continue
                # validate float attribute type
                if isinstance(atr['type'], str) and (atr['type'] == 'float'):
                    if name not in meta:
                        continue
                    if isinstance(meta[name], float):
                        print (f"{name}: IS_FLOAT")
                    else:
                        print (f"{name}: NOT_FLOAT")
                        errors.append(f"{name}: NOT_FLOAT")
                        continue
                # validate set attribute type                
                if isinstance(atr['type'], list):                                       
                    name_type = next(iter(atr['type'][0]))
                    arguments = atr['type'][0][name_type]
                    if name_type == 'set':
                        if name not in meta:
                            continue                    
                        try:
                            # get the elements of the set
                            if not meta[name] in arguments: # atr['type']:
                                print (f"{name}: INVALID_SET_VALUE")                        
                                errors.append(f"{name}: INVALID_SET_VALUE. {arguments}")
                                continue
                        except Exception as ex:
                            traceback.print_exc()
                            print (f"{name}: INVALID_CONFIG_SET")                        
                            errors.append(f"{name}: INVALID_CONFIG_SET")
                            continue 
        return errors










