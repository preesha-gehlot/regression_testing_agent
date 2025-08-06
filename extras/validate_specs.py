from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

if __name__ == "__main__":
    print("running")
    #spec_dict, base_uri = read_from_filename('tfl_openapi_spec.yaml')
    spec_dict, base_uri = read_from_filename('./endpoint_specs/get_BikePoint_Search.json')
    # If no exception is raised by validate(), the spec is valid.
    validate(spec_dict)